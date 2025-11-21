async function openInChatGPT(markdownPath) {
    // Get the full URL to the markdown file
    const fullUrl = window.location.origin + markdownPath;

    // Create a prompt asking ChatGPT to fetch and analyze the markdown file
    const prompt = encodeURIComponent(`Please fetch and analyze this Vespa documentation page: ${fullUrl} \n Await further instructions.`);

    window.open(`https://chatgpt.com/?q=${prompt}`, '_blank');
}