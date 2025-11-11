async function openInChatGPT(markdownPath) {
    try {
        const response = await fetch(markdownPath);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const markdown = await response.text();
        const encoded = encodeURIComponent(markdown);
        window.open(`https://chatgpt.com/?prompt=${encoded}`, '_blank');
    } catch (error) {
        console.error('Error fetching markdown:', error);
        alert('Could not fetch markdown content. Please try again.');
    }
}