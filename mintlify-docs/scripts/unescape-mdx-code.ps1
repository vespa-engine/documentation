# Remove unnecessary markdown escape backslashes inside ``` fences and inline `code`
$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$dirs = @("en\querying", "en\writing", "en\schemas")

function Unescape-CodeText([string]$text) {
    if ([string]::IsNullOrEmpty($text)) { return $text }

    $lines = $text -split "`n", -1
    $result = New-Object System.Collections.Generic.List[string]

    foreach ($line in $lines) {
        $trimmed = $line.TrimEnd()
        $trail = $line.Substring($trimmed.Length)
        $hasLineCont = $trimmed -match '\\$'

        if ($hasLineCont) {
            $work = $trimmed.Substring(0, $trimmed.Length - 1)
        } else {
            $work = $trimmed
        }

        $placeholder = @{}
        $i = 0
        $work = [regex]::Replace($work, '\\{2,}', {
            param($m)
            $key = "___BS$($i)___"
            $placeholder[$key] = $m.Value
            $script:i++
            return $key
        })
        $work = [regex]::Replace($work, '\\["'']', {
            param($m)
            $key = "___QS$($i)___"
            $placeholder[$key] = $m.Value
            $script:i++
            return $key
        })

        $work = $work -replace '\\([*_\[\]{}|.+#&?-])', '$1'

        foreach ($kv in $placeholder.GetEnumerator()) {
            $work = $work.Replace($kv.Key, $kv.Value)
        }

        if ($hasLineCont) { $work += '\' }
        $result.Add($work + $trail)
    }

    return ($result -join "`n")
}

function Process-InlineCode([string]$segment) {
    $parts = [regex]::Split($segment, '(`[^`]+`)')
    for ($j = 0; $j -lt $parts.Length; $j++) {
        if ($j % 2 -eq 1) {
            $inner = $parts[$j].Substring(1, $parts[$j].Length - 2)
            $parts[$j] = '`' + (Unescape-CodeText $inner) + '`'
        }
    }
    return ($parts -join '')
}

function Process-FenceBody([string]$body) {
    if ($body -match '^(?m)^') {
        $nl = $body.IndexOf("`n")
        if ($nl -lt 0) { return $body }
        $langLine = $body.Substring(0, $nl + 1)
        $code = $body.Substring($nl + 1)
        return $langLine + (Unescape-CodeText $code)
    }
    return (Unescape-CodeText $body)
}

$files = foreach ($d in $dirs) {
    Get-ChildItem (Join-Path $root $d) -Recurse -Filter "*.mdx"
}

foreach ($file in $files) {
    $content = [IO.File]::ReadAllText($file.FullName)
    $original = $content
    $parts = [regex]::Split($content, '(```)')
    $inFence = $false

    for ($i = 0; $i -lt $parts.Length; $i++) {
        $part = $parts[$i]
        if ($part -eq '```') {
            $inFence = -not $inFence
            continue
        }
        if ($inFence) {
            $parts[$i] = Process-FenceBody $part
        } else {
            $parts[$i] = Process-InlineCode $part
        }
    }

    $newContent = ($parts -join '')
    if ($newContent -ne $original) {
        [IO.File]::WriteAllText($file.FullName, $newContent)
        Write-Output "updated: $($file.Name)"
    }
}

Write-Output "done. $($files.Count) files scanned."
