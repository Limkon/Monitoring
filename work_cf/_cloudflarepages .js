export default {
    async fetch(request, env) {
        let url = new URL(request.url);

        if (url.pathname.startsWith('/')) {
            // 使用 PROXY_HOST 环境变量
            url.hostname = env.PROXY_HOST || "m3u8-player.com";

            let newRequest = new Request(url.toString(), {
                method: request.method,
                headers: request.headers,
                body: request.body,
                redirect: request.redirect
            });

            return fetch(newRequest);
        }

        return env.ASSETS.fetch(request);
    }
};
