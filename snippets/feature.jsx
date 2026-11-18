// One entry in a feature reference list, such as the rank feature reference.
//
//   import { Feature } from "/snippets/feature.jsx";
//
//   <Feature name="term(_n_).significance" default="0">
//
//   The description, written as ordinary Markdown.
//
//   </Feature>
//
// name     The feature name. _text_ renders italic. As in Markdown, an underscore
//          between two letters or digits is literal, so
//          name="matches_for_labels(_name_)" italicizes only "name". Write \_
//          for any other literal underscore. MDX attribute values are not
//          JavaScript strings, so that is a single backslash: name="\_x\_".
// default  The default value. Wrap it in backticks to render it as code. Leave
//          it out when the feature has no default.
// id       The anchor. It defaults to the name with the italic markers removed,
//          so term(_n_).significance is #term(n).significance. Set it to keep
//          an existing anchor that differs from the name.
//
// All layout decisions live here, so the whole list can be restyled by
// editing this file.

const MARKER = /(?<![\p{L}\p{N}\\])_(.+?)(?<!\\)_(?![\p{L}\p{N}])/gu;

const unescape = (text) => text.replace(/\\_/g, "_");

const parseName = (name) => {
  const parts = [];
  let last = 0;
  for (const match of name.matchAll(MARKER)) {
    if (match.index > last) {
      parts.push({ text: unescape(name.slice(last, match.index)) });
    }
    parts.push({ text: unescape(match[1]), italic: true });
    last = match.index + match[0].length;
  }
  if (last < name.length) {
    parts.push({ text: unescape(name.slice(last)) });
  }
  return parts;
};

const renderDefault = (value) => {
  const code = /^`(.+)`$/.exec(String(value));
  return code ? <code>{code[1]}</code> : value;
};

export const Feature = ({ name, default: def, id, children }) => {
  const parts = parseName(name);
  const anchor = id ?? parts.map((part) => part.text).join("");

  return (
    <div
      id={anchor}
      className="group scroll-mt-24 border-b border-gray-200 py-4 dark:border-gray-800"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <a
          href={`#${anchor}`}
          className="min-w-0 break-words font-semibold no-underline"
        >
          {parts.map((part, i) =>
            part.italic ? <em key={i}>{part.text}</em> : <span key={i}>{part.text}</span>
          )}
          <span
            aria-hidden="true"
            className="ml-2 font-normal text-gray-400 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100"
          >
            #
          </span>
        </a>
        {def !== undefined && def !== "" && (
          <span className="max-w-full break-words rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
            default: {renderDefault(def)}
          </span>
        )}
      </div>
      <div className="mt-2 text-sm leading-relaxed">{children}</div>
    </div>
  );
};
