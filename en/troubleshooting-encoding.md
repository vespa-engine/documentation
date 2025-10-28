---
# Copyright Vespa.ai. All rights reserved.
title: "Troubleshooting character encoding"
---

This document helps recognize the most common problems related to Unicode and I18N.

UTF-8 is a Unicode specific encoding where each letter (code point)
is encoded as one to four 8 bit bytes.
The UTF-8 schema can technically use more bytes,
but Unicode is defined as having approximately 1 million code points
(partly on cause of limitations of UTF-16),
and more than four bytes are then never necessary.

A string in Java is stored as UTF-16, a series of 16 bits char(acter)s.
All code points in Unicode base plane, the first 64k code points,
is represented as a single char, while higher code points is represented using surrogate pairs.
A surrogate pair is a pair of char from a reserved range.

Accessing a code point in a Java string is done using e.g. String.codePointAt(),
which then returns a 32-bit integer representing the code point (basically UCS-4).
When traversing a string in Java, use codePointAt + offsetByCodePoints
or String.codePoints() or similar methods.
If your applications conceptually handles letters,
using String.charAt() will most of the time be wrong.
To calculate buffer sizes for UTF-8 buffers with UTF-16 inputs without doing speculative encoding,
Vespa has a toolbox,
[com.yahoo.text.Utf8](https://github.com/vespa-engine/vespa/blob/master/vespajlib/src/main/java/com/yahoo/text/Utf8.java), with static helper methods.

If you are using python, use the following to remove control characters:

```
def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")
```

## Visual pattern matching of encoding bugs

| Transformation | Result |
| --- | --- |
| Input | hôtel |
| Correctly URL quoted (Vespa always uses UTF-8 there) | h%C3%B4tel |
| Encoded as ISO-8859-1 (ISO Latin-1), then URL quoted | h%F4tel |
| Encoded as UTF-16 (as in Java strings), then URL quoted | %00h%00%F4%00t%00e%00l |
| For completeness, little endian UTF-16, including byte order marker | %FF%FEh%00%F4%00t%00e%00l%00 |

What we are looking for is single bytes outside ASCII, i.e. ordinal above 127.
Given UTF-8, there should always be sequences of two or more of these
when a code point is outside ASCII.
The first byte for each code point will have the two most significant bits set,
in other words hex C to hex F.
The rest of the bytes for that code point will have the most significant bit set,
and the second most unset, in other words hex 8 to hex B.

From here, we move on to the two most common de-/encoding errors:

| Error | Hex dump of code points | Rendered |
| --- | --- | --- |
| UTF-8 input decoded as if it were ISO-8859-1 | h\xc3\xb4tel | hÃ´tel |
| UTF-8 input re-encoded as UTF-8, then decoded as UTF-8 again | h\xc3\xb4tel | hÃ´tel |

Note how these two bugs create exactly the same byte sequences.
This is because the first 256 code points of Unicode are identical to ISO-8859-1.
What we are looking for is line noise in-between normal ASCII,
as both ISO-8859-1 and Unicode are ASCII compatible.

Trying to decode valid ISO-8859-1 input with a UTF-8 decoder will usually make
the decoder report the input as invalid if there are code points outside ASCII.
Valid ISO-8859-1 rarely end up conforming to the required bit patterns of valid UTF-8,
though it sometimes happens.
*Never* try to debug encoding problems with a web browser.
Always use a hexdump tool.
`xxd` is a nice utility which is included with vim,
which avoids several of the endianness headaches associated with some UNIX alternatives.

Also, remember Windows 1252 is *not* the same as ISO-8859-1.

## JSON

Use proper JSON - a common error is not stripping ASCII control characters from feed data.
See [stripInvalidCharacters](https://github.com/vespa-engine/vespa/blob/master/vespajlib/src/main/java/com/yahoo/text/Text.java) for a utility function.
