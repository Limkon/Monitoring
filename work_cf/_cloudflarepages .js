export default {
    async fetch(request, env) {
        let url = new URL(request.url);

        // 检查路径是否符合你的自定义逻辑（如检查路径或其他条件）
        if (url.pathname.startsWith('/')) {
            // 通过拼接的方式设置主机名（url.hostname 是只读的）
            let newUrl = `${request.url.replace(url.hostname, env.HOSTNAME || "m3u8-player.com")}`;

            // 创建新请求，保留原始请求的所有属性
            let newRequest = new Request(newUrl, {
                method: request.method,
                headers: request.headers,
                body: request.body,
                redirect: request.redirect
            });

            // 发送更新后的请求
            return fetch(newRequest);
        }

        // 如果路径不符合条件，则从 ASSETS 中获取请求
        return env.ASSETS.fetch(request);
    }
};
