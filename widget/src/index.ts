import { mount, unmount } from "svelte";
import Widget from "./Widget.svelte";

export interface WidgetProps {
    element?: string | HTMLElement;
    chatfaqApi?: string;
    chatfaqWs?: string;
    fsmDef?: string;
    userId?: string;
    title?: string;
    subtitle?: string;
    widgetConfigId?: string;
    conversationId?: string;
    lang?: string;
    previewMode?: boolean;
    customCss?: string;
    hideSources?: boolean;
    sourcesFirst?: boolean;
    startWithHistoryClosed?: boolean;
    startSmallMode?: boolean;
    fullScreen?: boolean;
    onlyChat?: boolean;
    noMenu?: boolean;
    fitToParent?: boolean;
    [key: string]: unknown;
}

function datasetProps(element: HTMLElement): WidgetProps {
    const props: WidgetProps = {};
    for (const [key, value] of Object.entries(element.dataset)) {
        props[key] = value === "" ? true : value;
    }
    return props;
}

export class ChatfaqWidget {
    element: HTMLElement;
    private app: Record<string, unknown> | undefined;

    constructor(attrs: WidgetProps) {
        const element = typeof attrs.element === "string" ? document.querySelector(attrs.element) : attrs.element;
        if (!element) {
            throw new Error("ChatfaqWidget element was not found");
        }
        this.element = element;
        this.props = { ...datasetProps(element), ...attrs };
    }

    private props: WidgetProps;

    mount() {
        this.app = mount(Widget, { target: this.element, props: this.props });
        return this.app;
    }
}

export class ChatfaqWidgetCustomElement extends HTMLElement {
    private app: Record<string, unknown> | undefined;

    connectedCallback() {
        this.app = mount(Widget, { target: this, props: datasetProps(this) });
    }

    disconnectedCallback() {
        if (this.app) {
            unmount(this.app);
        }
    }
}
