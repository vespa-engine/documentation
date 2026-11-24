// One entry in a reference list: a rank feature, a configuration property,
// a query parameter, a query operator and so on.
//
//   import { Entry } from "/snippets/entry.jsx";
//
//   <Entry name="term(_n_).significance" default="0">
//
//   The description, written as ordinary Markdown.
//
//   </Entry>
//
// name     The name of the entry. _text_ renders italic. As in Markdown, an
//          underscore between two letters or digits is literal, so
//          name="matches_for_labels(_name_)" italicizes only "name". Write \_
//          for any other literal underscore. MDX attribute values are not
//          JavaScript strings, so that is a single backslash: name="\_x\_".
// alias    Other names for the entry, rendered like the name. Optional.
// presence Whether the entry is required, such as required or optional.
//          Shown first, capitalized, without a label. Optional.
// occurrence
//          How many times the entry may occur, such as One or Optional.
//          Optional.
// type     The type or allowed values, shown in monospace. Surrounding
//          backticks are ignored. Optional.
// typeHref A link for the type, such as "#model-config-reference". Optional.
// default  The default value, shown in monospace. Surrounding backticks are
//          ignored. Leave it out when there is no default.
// defaultHref
//          A link for the default value. Optional.
// id       The anchor. It defaults to the name with the italic markers removed,
//          so term(_n_).significance is #term(n).significance. Set it to keep
//          an existing anchor that differs from the name.
//
// Use plain string attributes only. Mintlify drops expression attributes
// such as type={...} when a page is edited in its web editor.
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

const stripBackticks = (value) => String(value).replace(/^`(.+)`$/, "$1");

export const Entry = ({ name, alias, presence, occurrence, type, typeHref, default: def, defaultHref, id, children }) => {
  const parts = parseName(name);
  const anchor = id ?? parts.map((part) => part.text).join("");
  const hasAlias = alias !== undefined && alias !== "";
  const hasPresence = presence !== undefined && presence !== "";
  const hasOccurrence = occurrence !== undefined && occurrence !== "";
  const hasType = type !== undefined && type !== "";
  const hasDefault = def !== undefined && def !== "";

  return (
    <div
      id={anchor}
      className="group my-6 scroll-mt-24 border-l-2 border-gray-200 py-0.5 pl-4 hover:border-gray-400 dark:border-gray-700 dark:hover:border-gray-500"
    >
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <a
          href={`#${anchor}`}
          className="min-w-0 break-words border-none font-mono text-sm font-bold text-gray-900 no-underline dark:text-gray-100"
        >
          {/* strong, because Mintlify resets the weight of other descendants */}
          <strong>
            {parts.map((part, i) =>
              part.italic ? <em key={i}>{part.text}</em> : <span key={i}>{part.text}</span>
            )}
          </strong>
          <span
            aria-hidden="true"
            className="ml-2 font-sans font-normal text-gray-400 opacity-0 group-hover:opacity-100 group-focus-within:opacity-100"
          >
            #
          </span>
        </a>
        {(hasPresence || hasAlias || hasOccurrence || hasType || hasDefault) && (
          // strong, because Mintlify resets the weight of other descendants
          <strong className="flex max-w-full flex-wrap gap-x-4 break-words text-xs font-semibold text-gray-500 dark:text-gray-400">
            {hasPresence && (
              <span className="text-gray-800 dark:text-gray-200">
                {presence.charAt(0).toUpperCase() + presence.slice(1)}
              </span>
            )}
            {hasAlias && (
              <span>
                Alias ={" "}
                <span className="font-mono text-gray-800 dark:text-gray-200">
                  {parseName(alias).map((part, i) =>
                    part.italic ? <em key={i}>{part.text}</em> : <span key={i}>{part.text}</span>
                  )}
                </span>
              </span>
            )}
            {hasOccurrence && (
              <span>
                Occurrence ={" "}
                <span className="font-mono text-gray-800 dark:text-gray-200">{occurrence}</span>
              </span>
            )}
            {hasType && (
              <span>
                Type ={" "}
                {typeHref ? (
                  <a href={typeHref} className="font-mono text-gray-800 dark:text-gray-200">
                    {stripBackticks(type)}
                  </a>
                ) : (
                  <span className="font-mono text-gray-800 dark:text-gray-200">{stripBackticks(type)}</span>
                )}
              </span>
            )}
            {hasDefault && (
              <span>
                Default ={" "}
                {defaultHref ? (
                  <a href={defaultHref} className="font-mono text-gray-800 dark:text-gray-200">
                    {stripBackticks(def)}
                  </a>
                ) : (
                  <span className="font-mono text-gray-800 dark:text-gray-200">{stripBackticks(def)}</span>
                )}
              </span>
            )}
          </strong>
        )}
      </div>
      <div className="prose-sm mt-1">{children}</div>
    </div>
  );
};
