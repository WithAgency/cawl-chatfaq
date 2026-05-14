<template>
    <div class="conversation-feedback">
        <div
            v-if="!store.conversationFeedbackSent"
            class="feedback-toggle"
            @click="showForm = true"
        >
            {{ $t('conversation_feedback_evaluate') }}
        </div>
        <div v-if="showForm" class="feedback-backdrop" @click.self="closePanel">
            <div class="feedback-panel" :class="{ 'dark-mode': store.darkMode }">
                <div class="panel-header">
                    <h3>{{ $t('conversation_feedback_title') }}</h3>
                    <Close class="close-icon" @click="closePanel" />
                </div>
                <p class="panel-desc">{{ $t('conversation_feedback_desc') }}</p>
                <div class="tags-grid">
                    <div
                        v-for="tag in tags"
                        :key="tag.key"
                        class="tag-chip"
                        :class="{ selected: selectedTags.includes(tag.key), 'dark-mode': store.darkMode }"
                        @click="toggleTag(tag.key)"
                    >
                        <div class="tag-checkbox">
                            <Check v-if="selectedTags.includes(tag.key)" class="check-icon" />
                        </div>
                        <span class="tag-label">{{ $t(tag.label) }}</span>
                        <div class="tag-info-icon" :title="$t(tag.hover)">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <circle cx="8" cy="8" r="6.5" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M8 5V8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                <circle cx="8" cy="11" r="0.75" fill="currentColor"/>
                            </svg>
                        </div>
                    </div>
                </div>
                <div class="comment-wrapper">
                    <textarea
                        v-model="comment"
                        class="comment-input"
                        :class="{ 'dark-mode': store.darkMode }"
                        :placeholder="$t('conversation_feedback_comment_placeholder')"
                        maxlength="300"
                        rows="3"
                    ></textarea>
                    <span class="char-count">{{ comment.length }}/300</span>
                </div>
                <button
                    class="send-btn"
                    :class="{ disabled: selectedTags.length === 0, 'dark-mode': store.darkMode }"
                    :disabled="selectedTags.length === 0 || submitting"
                    @click="submitFeedback"
                >
                    {{ $t('conversation_feedback_send') }}
                </button>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref, watch } from "vue";
import { useGlobalStore } from "~/store";
import Close from "~/components/icons/Close.vue";
import Check from "~/components/icons/Check.vue";

const store = useGlobalStore();

const showForm = ref(false);
const submitting = ref(false);
const selectedTags = ref([]);
const comment = ref("");

const tags = [
    { key: "wrong_business_logic", label: "tag_wrong_business_logic", hover: "tag_wrong_business_logic_hover" },
    { key: "safeguard_not_respected", label: "tag_safeguard_not_respected", hover: "tag_safeguard_not_respected_hover" },
    { key: "insufficient_conversation_quality", label: "tag_insufficient_conversation_quality", hover: "tag_insufficient_conversation_quality_hover" },
    { key: "rag_error", label: "tag_rag_error", hover: "tag_rag_error_hover" },
    { key: "conversion_incorrect", label: "tag_conversion_incorrect", hover: "tag_conversion_incorrect_hover" },
    { key: "technical_robustness", label: "tag_technical_robustness", hover: "tag_technical_robustness_hover" },
    { key: "ai_non_conformity", label: "tag_ai_non_conformity", hover: "tag_ai_non_conformity_hover" },
    { key: "multi_turn_inconsistency", label: "tag_multi_turn_inconsistency", hover: "tag_multi_turn_inconsistency_hover" },
];

watch(() => store.selectedPlConversationId, () => {
    store.conversationFeedbackSent = false;
});

function toggleTag(key) {
    const idx = selectedTags.value.indexOf(key);
    if (idx === -1)
        selectedTags.value.push(key);
    else
        selectedTags.value.splice(idx, 1);
}

function closePanel() {
    showForm.value = false;
}

async function submitFeedback() {
    if (selectedTags.value.length === 0 || submitting.value)
        return;

    submitting.value = true;

    const payload = {
        conversation_id: store.selectedPlConversationId,
        tags: selectedTags.value,
        comment: comment.value.trim(),
    };

    if (store.previewMode) {
        submitting.value = false;
        store.conversationFeedbackSent = true;
        showForm.value = false;
        return;
    }

    const headers = { 'Content-Type': 'application/json' };
    if (store.authToken)
        headers.Authorization = `Token ${store.authToken}`;

    try {
        await chatfaqFetch(store.chatfaqAPI + '/back/api/broker/conversation-feedback/', {
            method: 'POST',
            headers,
            body: JSON.stringify(payload),
        });
        store.conversationFeedbackSent = true;
        showForm.value = false;
    } catch (e) {
        console.error("Feedback submission failed", e);
    } finally {
        submitting.value = false;
    }
}
</script>

<style lang="scss" scoped>
.conversation-feedback {
    .feedback-toggle {
        cursor: pointer;
        background: $chatfaq-color-feedbackToggle-background;
        color: $chatfaq-color-feedbackToggle-text;
        font: $chatfaq-feedbackToggle-font;
        padding: 8px 16px;
        border-radius: 100px;
        white-space: nowrap;
        font-size: 12px;
        text-transform: uppercase;

        &:hover {
            opacity: 0.9;
        }
    }

    .feedback-backdrop {
        position: fixed;
        inset: 0;
        z-index: 10000;
        background: $chatfaq-color-darkFilter;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .feedback-panel {
        background: $chatfaq-color-feedbackPanel-background;
        border-radius: 16px;
        width: 520px;
        max-width: calc(100vw - 32px);
        max-height: calc(100vh - 32px);
        overflow-y: auto;
        padding: 28px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);

        &.dark-mode {
            background: $chatfaq-color-feedbackPanel-background-dark;
            color: $chatfaq-color-feedbackPanel-text-dark;
        }
    }

    .panel-header {
        display: flex;
        align-items: center;
        justify-content: space-between;

        h3 {
            font: $chatfaq-font-body-m-bold;
            margin: 0;
            color: $chatfaq-color-feedbackPanel-title-text;

            .dark-mode & {
                color: $chatfaq-color-feedbackPanel-title-text-dark;
            }
        }

        .close-icon {
            cursor: pointer;
            color: $chatfaq-color-feedbackCloseIcon-color;
            width: 24px;
            height: 24px;
            flex-shrink: 0;

            &:hover {
                color: $chatfaq-color-feedbackCloseIcon-hoverColor;

                .dark-mode & {
                    color: $chatfaq-color-feedbackCloseIcon-hoverColor-dark;
                }
            }
        }
    }

    .panel-desc {
        font: $chatfaq-font-body-s;
        color: $chatfaq-color-feedbackPanel-desc-text;
        margin: 0;
        line-height: 1.5;

        .dark-mode & {
            color: $chatfaq-color-feedbackPanel-desc-text-dark;
        }
    }

    .tags-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .tag-chip {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 12px;
        border-radius: 8px;
        cursor: pointer;
        background: $chatfaq-color-feedbackTag-background;
        border: 1px solid $chatfaq-color-feedbackTag-border;
        transition: all 0.15s ease;
        user-select: none;

        &.dark-mode {
            background: $chatfaq-color-feedbackTag-background-dark;
            border-color: $chatfaq-color-feedbackTag-border-dark;
        }

        &:hover {
            border-color: $chatfaq-color-feedbackTag-hoverBorder;
            background: $chatfaq-color-feedbackTag-hoverBackground;
        }

        &.selected {
            background: $chatfaq-color-feedbackTag-selectedBackground;
            border-color: $chatfaq-color-feedbackTag-selectedBorder;

            .tag-label {
                color: $chatfaq-color-feedbackTag-selectedLabelText;
            }

            .tag-checkbox {
                background: $chatfaq-color-feedbackTag-selectedCheckboxBackground;
                border-color: $chatfaq-color-feedbackTag-selectedCheckboxBorder;

                .check-icon {
                    color: $chatfaq-color-feedbackTag-selectedCheckIcon;
                }
            }

            .tag-info-icon {
                color: $chatfaq-color-feedbackTag-selectedInfoIcon;
            }
        }
    }

    .tag-checkbox {
        width: 16px;
        height: 16px;
        border: 1.5px solid $chatfaq-color-feedbackCheckbox-border;
        border-radius: 3px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        transition: all 0.15s ease;

        .dark-mode & {
            border-color: $chatfaq-color-feedbackCheckbox-border-dark;
        }

        .check-icon {
            width: 12px;
            height: 12px;
        }
    }

    .tag-label {
        font: $chatfaq-font-body-s;
        color: $chatfaq-color-feedbackTagLabel-text;
        white-space: nowrap;

        .dark-mode & {
            color: $chatfaq-color-feedbackTagLabel-text-dark;
        }
    }

    .tag-info-icon {
        color: $chatfaq-color-feedbackInfoIcon-color;
        width: 16px;
        height: 16px;
        flex-shrink: 0;
        cursor: help;

        .dark-mode & {
            color: $chatfaq-color-feedbackInfoIcon-color-dark;
        }
    }

    .comment-wrapper {
        position: relative;

        .comment-input {
            width: 100%;
            border: 1px solid $chatfaq-color-feedbackInput-border;
            border-radius: 8px;
            padding: 12px 16px;
            font: $chatfaq-font-body-s;
            color: $chatfaq-color-feedbackInput-text;
            background: $chatfaq-color-feedbackInput-background;
            resize: none;
            box-sizing: border-box;
            line-height: 1.5;

            &.dark-mode {
                background: $chatfaq-color-feedbackInput-background-dark;
                border-color: $chatfaq-color-feedbackInput-border-dark;
                color: $chatfaq-color-feedbackInput-text-dark;
            }

            &::placeholder {
                color: $chatfaq-color-feedbackInput-placeholder;
                font-style: italic;

                .dark-mode & {
                    color: $chatfaq-color-feedbackInput-placeholder-dark;
                }
            }

            &:focus {
                outline: none;
                border-color: $chatfaq-color-feedbackInput-focusBorder;
            }
        }

        .char-count {
            position: absolute;
            bottom: 8px;
            right: 12px;
            font-size: 11px;
            color: $chatfaq-color-feedbackCharCount-color;
        }
    }

    .send-btn {
        align-self: flex-end;
        cursor: pointer;
        background: $chatfaq-color-feedbackSendButton-background;
        color: $chatfaq-color-feedbackSendButton-text;
        font: $chatfaq-font-button;
        font-size: 14px;
        padding: 10px 24px;
        border: none;
        border-radius: 100px;
        text-transform: uppercase;
        transition: opacity 0.15s ease;

        &:hover:not(.disabled) {
            opacity: 0.9;
        }

        &.disabled {
            opacity: 0.4;
            cursor: not-allowed;
        }

        &.dark-mode {
            background: $chatfaq-color-feedbackSendButton-background-dark;
        }
    }
}
</style>
