import type { Component } from "solid-js"
import { createMemo } from "solid-js"

export enum ButtonPreset {
  DEFAULT,
  ERROR,
  WARNING,
}
const Button: Component<{
  preset?: ButtonPreset
  title: string
  click?: () => void
}> = p => {
  const commonClass = "flex-1 border-1px p-2 rounded-2 cursor-pointer select-none text-center"
  const presetClass = createMemo(() => {
    let classes = " "
    switch (p.preset) {
      case ButtonPreset.ERROR:
        classes += ""
        break
      case ButtonPreset.WARNING:
        classes += ""
        break
      case ButtonPreset.DEFAULT:
      default:
        classes += "border-gray active:(bg-gray/30) hover:(bg-gray/10)"
        break
    }
    return classes
  })
  return (
    <div class={commonClass + presetClass()} onClick={p.click}>
      {p.title}
    </div>
  )
}

export default Button
