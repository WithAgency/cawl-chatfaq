<template>
    <client-only>
        <Widget :chatfaqWs="chatfaqWS" :chatfaqApi="chatfaqAPI" :fsmDef="fsmDef" :title="title"
                :subtitle="subtitle" enable-logout :allow-attachments="true"
                :hideSources="hideSources" :stateOverride="stateOverride" :widgetConfigId="widgetId"
                splitScreenIframe="http://localhost:3001/right-panel"
                :enable-conversation-feedback="true"
        />
    </client-only>
</template>
<script setup>
const conf = useRuntimeConfig()

const requestUrl = useRequestURL()
const chatfaqWS = ref(conf.public.chatfaqWS)
const chatfaqAPI = ref(conf.public.chatfaqAPI)
const title = ref("Hello there 👋")
const fsmDef = ref("llm_fsm")
const hideSources = ref(false)
const stateOverride = ref(requestUrl.searchParams.get("state_override"))
const widgetId = ref(requestUrl.searchParams.get("widget_id") || "6a5fb833-cdcf-468a-ac22-8f1c2b7b1672")
</script>
