Tensor playground

(function() {
// Check for saved theme preference
let savedTheme = localStorage.getItem('theme');
// If no saved preference, check system preference
if (!savedTheme) {
savedTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}
// Apply theme immediately before page renders
document.documentElement.setAttribute('data-theme', savedTheme);
})();

[![Vespa logo](/assets/logos/logo.svg)](/playground)

Tensor Playground

[View setup](#)
[Clear](#)
[Copy url](#)
[Toggle dark mode](#)

The tensor playground is a tool to get familiar with tensor algebra.
For more information see [Tensor Examples](/en/tensor-examples.html),
[Introduction to Vespa Tensors](https://blog.vespa.ai/computing-with-tensors/)
and [Advent of Tensors](https://blog.vespa.ai/advent-of-tensors-2023/).

Select example ...

Dense tensor dot product

Sparse tensor dot product

Vector-matrix product

Matrix multiplication

Tensor generation, dimension renaming and concatenation

Jaccard similarity between mapped (sparse) tensors

Neural network

[Apply](#)
[Close](#)

[New comment](#)
[New expression](#)

|  |  |
| --- | --- |
| Command | Action |
| Up / k | Select previous frame |
| Down / j | Select next frame |
| Shift + Up / Shift + k | Move frame up |
| Shift + Down / Shift + j | Move frame down |
| Enter / e | Edit selected frame |
| Ctrl + Enter | Save and execute frame |
| Esc | Cancel editing of frame |
| x / d then d | Remove selected frame |
| Ctrl + Enter | Execute frame and all frames below |
| n then c | Add new comment below selected frame |
| n then e | Add new expression below selected frame |
