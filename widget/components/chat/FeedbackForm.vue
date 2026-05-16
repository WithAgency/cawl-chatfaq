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
            <div class="feedback-panel" :class="{ 'dark-mode': store.darkMode }" @click.self="closeTooltip">
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
                        <div
                            class="tag-info-icon"
                            @mouseenter="activeTooltip = tag.key"
                            @mouseleave="activeTooltip = null"
                            @click.stop="toggleTooltip(tag.key)"
                        >
                            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M10 6.5V10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                                <circle cx="10" cy="13.5" r="1" fill="currentColor"/>
                            </svg>
                            <div v-if="activeTooltip === tag.key" ref="tooltipRef" class="tooltip-popup" :style="tooltipStyle">
                                {{ $t(tag.hover) }}
                                <div class="tooltip-arrow"></div>
                            </div>
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
import { ref, watch, nextTick } from "vue";
import { useGlobalStore } from "~/store";
import Close from "~/components/icons/Close.vue";
import Check from "~/components/icons/Check.vue";

const store = useGlobalStore();

const showForm = ref(false);
const submitting = ref(false);
const selectedTags = ref([]);
const comment = ref("");
const activeTooltip = ref(null);
const tooltipRef = ref(null);
const tooltipStyle = ref({});

watch(activeTooltip, async () => {
    tooltipStyle.value = {};
    if (activeTooltip.value) {
        await nextTick();
        const el = Array.isArray(tooltipRef.value) ? tooltipRef.value[0] : tooltipRef.value;
        if (el) {
            const rect = el.getBoundingClientRect();
            const shift = { x: 0 };
            const margin = 24;
            if (rect.right > window.innerWidth - margin)
                shift.x = window.innerWidth - margin - rect.right;
            if (rect.left < margin)
                shift.x = margin - rect.left;
            if (shift.x)
                tooltipStyle.value = { transform: `translateX(calc(-50% + ${shift.x}px))` };
        }
    }
});

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

function toggleTooltip(key) {
    if (activeTooltip.value === key)
        activeTooltip.value = null;
    else
        activeTooltip.value = key;
}

function closePanel() {
    showForm.value = false;
    activeTooltip.value = null;
}

function closeTooltip() {
    activeTooltip.value = null;
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
        padding: 10px 20px;
        border-radius: 100px;
        white-space: nowrap;
        font-size: 14px;

        &:hover {
            opacity: 0.9;
        }
    }

    .feedback-backdrop {
        position: absolute;
        inset: 0;
        z-index: 10000;
        background: $chatfaq-color-feedbackBackdrop;
        backdrop-filter: blur(6px);
        border-radius: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .feedback-panel {
        background: $chatfaq-color-feedbackPanel-background;
        border-radius: 20px;
        width: 520px;
        max-width: calc(100vw - 32px);
        max-height: calc(100vh - 32px);
        overflow-y: auto;
        padding: 24px;
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
        gap: 10px;
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
        width: 12px;
        height: 12px;
        border: 1px solid $chatfaq-color-feedbackCheckbox-border;
        border-radius: 2px;
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
        width: 20px;
        height: 20px;
        flex-shrink: 0;
        cursor: help;
        position: relative;

        .dark-mode & {
            color: $chatfaq-color-feedbackInfoIcon-color-dark;
        }
    }

    .tooltip-popup {
        position: absolute;
        bottom: calc(100% + 8px);
        left: 50%;
        transform: translateX(-50%);
        background: $chatfaq-color-feedbackTooltip-background;
        border: 1px solid $chatfaq-color-feedbackTooltip-border;
        border-radius: 8px;
        padding: 6px 12px;
        width: 235px;
        font: $chatfaq-font-feedbackTooltip;
        color: $chatfaq-color-feedbackTooltip-text;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.06);
        z-index: 10001;
        pointer-events: none;
    }

    .tooltip-arrow {
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%) rotate(45deg);
        width: 8.5px;
        height: 8.5px;
        background: $chatfaq-color-feedbackTooltip-background;
        border-right: 1px solid $chatfaq-color-feedbackTooltip-border;
        border-bottom: 1px solid $chatfaq-color-feedbackTooltip-border;
        margin-top: -4.25px;
    }

    .comment-wrapper {
        position: relative;

        .comment-input {
            width: 100%;
            border: 1px solid $chatfaq-color-feedbackInput-border;
            border-radius: 4px;
            padding: 10px 16px;
            min-height: 74px;
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
        align-self: flex-start;
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
