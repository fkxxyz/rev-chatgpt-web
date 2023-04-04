import { defineConfig, presetAttributify, presetUno, presetIcons } from "unocss"
import { presetForms } from "@julr/unocss-preset-forms"
import transformerVariantGroup from "@unocss/transformer-variant-group"

export default defineConfig({
  presets: [presetAttributify(), presetUno(), presetForms(), presetIcons()],
  shortcuts: {
    xyc: "justify-center items-center",
  },
  transformers: [transformerVariantGroup()],
})
