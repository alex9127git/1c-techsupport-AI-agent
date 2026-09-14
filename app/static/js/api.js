(function (root) {
    "use strict";

    function call(method, path, body, isForm) {
        var options = { method: method };
        if (body !== undefined) {
            if (isForm) {
                options.body = body;
            } else {
                options.headers = { "Content-Type": "application/json" };
                options.body = JSON.stringify(body);
            }
        }
        return fetch(path, options).then(function (resp) {
            return resp.json().catch(function () {
                return { ok: false, error: { code: "parse_error", message: "Неверный ответ сервера" }, http_status: resp.status };
            });
        });
    }

    function getNumbers(data) {
        return data || {};
    }

    root.API = {
        chat: function (message, history) {
            return call("POST", "/api/chat", { message: message, history: history || [] });
        },
        chatImage: function (file, message) {
            var form = new FormData();
            form.append("file", file);
            if (message) form.append("message", message);
            return call("POST", "/api/chat/image", form, true);
        },
        kbList: function () {
            return call("GET", "/api/kb");
        },
        kbCreate: function (title, content, tags) {
            return call("POST", "/api/kb", { title: title, content: content || "", tags: tags || [] });
        },
        kbUpload: function (file, title) {
            var form = new FormData();
            form.append("file", file);
            if (title) form.append("title", title);
            return call("POST", "/api/kb/upload", form, true);
        },
        kbDelete: function (id) {
            return call("DELETE", "/api/kb/" + id);
        },
        dashboard: function () {
            return call("GET", "/api/dashboard");
        },
        settingsGet: function () {
            return call("GET", "/api/settings");
        },
        settingsPut: function (body) {
            return call("PUT", "/api/settings", body);
        },
        escalations: function () {
            return call("GET", "/api/escalations");
        },
        integrations: function () {
            return call("GET", "/api/integrations");
        },
        logs: function () {
            return call("GET", "/api/logs");
        },
        errorMessage: function (payload) {
            if (payload && payload.error && payload.error.message) return payload.error.message;
            return "Сервер недоступен";
        },
        getNumbers: getNumbers
    };
})(window);