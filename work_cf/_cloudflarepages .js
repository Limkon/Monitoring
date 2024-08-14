export default {
    async fetch(request, env) {
        // 从请求中提取当前 URL
        let url = new URL(request.url);

        // 检查路径是否以 '/' 开头，并且是否设置了主机名的环境变量
        if (url.pathname.startsWith('/')) {
            // 使用环境变量设置主机名
            url.hostname = env.CUSTOM_HOSTNAME || "default.hostname.com";

            // 使用更新后的 URL 创建新的请求
            let new_request = new Request(url, request);

            // 发送更新后的请求
            return fetch(new_request);
        }

        // 如果路径不是以 '/' 开头，则从 ASSETS 中获取请求
        return env.ASSETS.fetch(request);
    }
};
