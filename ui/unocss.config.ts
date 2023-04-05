import { defineConfig, presetAttributify, presetUno, presetIcons } from "unocss"
import { presetForms } from "@julr/unocss-preset-forms"
import transformerVariantGroup from "@unocss/transformer-variant-group"
import { presetScrollbar } from "unocss-preset-scrollbar"

export default defineConfig({
  presets: [presetAttributify(), presetUno(), presetForms(), presetIcons(), presetScrollbar()],
  shortcuts: {
    xyc: "justify-center items-center",
  },
  transformers: [transformerVariantGroup()],
})
