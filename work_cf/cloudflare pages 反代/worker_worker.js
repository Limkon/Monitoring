export default {
    async fetch(request, env) {
        let url = new URL(request.url);

        // 如果请求的路径以 '/' 开头（表示有效路径）
        if (url.pathname.startsWith('/')) {
            // 设置自定义的主机名（如果没有设置，则使用默认值）
            url.hostname = env.CUSTOM_HOSTNAME || "c729.celestialin.workers.dev";

            // 创建新的请求，继承原请求的方法、头信息和 body
            let new_request = new Request(url, {
                method: request.method,
                headers: request.headers,
                body: request.method !== "GET" && request.method !== "HEAD" ? request.body : null,
                redirect: "follow"
            });

            // 发送新的请求
            return fetch(new_request);
        }

        // 默认情况下，直接返回原始请求
        return fetch(request);
    }
};
