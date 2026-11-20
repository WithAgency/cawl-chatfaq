"""Generate the TypeScript client for the stable DRF endpoints the front calls."""

import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.urls import include, path
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.renderers import OpenApiYamlRenderer
from knox import views as knox_views

from back.apps.people.views import LoginView


class Command(BaseCommand):
    """Generate a TypeScript client from login, logout and the people API."""

    help = "Generate the TypeScript client from the front-facing DRF schema"

    def get_schema(self) -> bytes:
        """Build a schema limited to the endpoints the SvelteKit server calls."""
        patterns = [
            path("back/api/login/", LoginView.as_view(), name="knox_login"),
            path("back/api/logout/", knox_views.LogoutView.as_view(), name="knox_logout"),
            path("back/api/people/", include("back.apps.people.urls")),
        ]
        generator = SchemaGenerator(patterns=patterns)
        schema = generator.get_schema(request=None, public=True)
        return OpenApiYamlRenderer().render(schema, renderer_context={})

    def create_client(self, workdir: Path) -> None:
        """Run OpenAPI Generator in a temporary directory."""
        try:
            from openapi_generator_cli import run as run_oag
        except ImportError as exc:
            raise CommandError(
                "openapi-generator-cli is not installed. Add it to the test group before regenerating."
            ) from exc

        run_oag(
            [
                "generate",
                *["-i", str(workdir / "schema.yaml")],
                *["-g", "typescript-fetch"],
                *["-o", str(workdir / "client")],
                "--additional-properties=useSingleRequestParameter=false",
            ]
        )

    def copy_client(self, workdir: Path) -> None:
        """Copy the generated client into the frontend source tree."""
        repo_root = Path(settings.BASE_DIR).parent
        target_dir = repo_root / "front" / "src" / "lib" / "client"
        shutil.rmtree(target_dir, ignore_errors=True)
        shutil.copytree(workdir / "client", target_dir)
        shutil.rmtree(target_dir / ".openapi-generator", ignore_errors=True)
        (target_dir / ".openapi-generator-ignore").unlink(missing_ok=True)

    def format_client(self) -> None:
        """Format the generated TypeScript client with the frontend formatter."""
        front_dir = Path(settings.BASE_DIR).parent / "front"
        pnpm = shutil.which("pnpm")
        if pnpm is None:
            raise CommandError("Could not find pnpm to format the generated TypeScript client.")
        subprocess.run(
            [pnpm, "exec", "prettier", "--write", "src/lib/client/**/*.ts"],
            cwd=front_dir,
            check=True,
        )

    def handle(self, *args, **options) -> None:
        """Generate the schema, run the TS generator, then copy the result."""
        with TemporaryDirectory() as workdir_str:
            workdir = Path(workdir_str)
            (workdir / "schema.yaml").write_bytes(self.get_schema())
            self.create_client(workdir)
            self.copy_client(workdir)
            self.format_client()
