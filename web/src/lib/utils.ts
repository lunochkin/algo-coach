import { createCn } from 'cn/config'

// the type scale is named by role, and the merge cannot tell `text-meta` from
// a colour: it dropped the size whenever a state added `text-*-foreground`
export const cn = createCn({
  extend: {
    // `text-code-keyword` and its four are colours, and the group matches the
    // role names exactly, so they are untouched
    classGroups: {
      'font-size': [{ text: ['title', 'heading', 'body', 'meta', 'code', 'code-inline'] }],
    },
  },
})
