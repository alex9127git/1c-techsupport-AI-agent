(function () {
    "use strict";

    function el(id) {
        return document.getElementById(id);
    }

    function renderResult(targetId, payload) {
        var node = el(targetId);
        if (!node) return;
        node.classList.remove("ok", "error", "pending", "not-impl");
        if (payload.pending) {
            node.textContent = payload.text || "Запрос выполняется…";
            node.classList.add("pending");
            return;
        }
        var text = JSON.stringify(payload.data || payload, null, 2);
        node.textContent = text;
        if (payload.ok === false) {
            node.classList.add("error");
        } else if (payload.notImplemented) {
            node.classList.add("not-impl");
        } else {
            node.classList.add("ok");
        }
    }

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
                return { ok: false, error: { code: "parse_error", message: "Не JSON ответ" }, http_status: resp.status };
            });
        });
    }

    function markNotImplemented(payload) {
        var data = payload.data;
        if (payload.ok && data && typeof data.status === "string" && data.status === "not_implemented") {
            payload.notImplemented = true;
        }
        return payload;
    }

    function submitChat() {
        var message = el("chat-message").value;
        if (!message) {
            renderResult("chat-result", { ok: false, error: { code: "validation", message: "Введите вопрос" } });
            return;
        }
        renderResult("chat-result", { pending: true });
        call("POST", "/api/chat", { message: message })
            .then(markNotImplemented)
            .then(function (p) { renderResult("chat-result", p); });
    }

    function submitImage() {
        var file = el("image-file").files[0];
        if (!file) {
            renderResult("image-result", { ok: false, error: { code: "validation", message: "Выберите файл" } });
            return;
        }
        var form = new FormData();
        form.append("file", file);
        var message = el("image-message").value;
        if (message) form.append("message", message);
        renderResult("image-result", { pending: true });
        call("POST", "/api/chat/image", form, true)
            .then(markNotImplemented)
            .then(function (p) { renderResult("image-result", p); });
    }

    function kbList() {
        renderResult("kb-result", { pending: true });
        call("GET", "/api/kb").then(function (p) { renderResult("kb-result", p); });
    }

    function kbCreate() {
        var title = el("kb-title").value;
        if (!title) {
            renderResult("kb-result", { ok: false, error: { code: "validation", message: "Введите заголовок" } });
            return;
        }
        var tags = el("kb-tags").value
            .split(",")
            .map(function (t) { return t.trim(); })
            .filter(Boolean);
        var content = el("kb-content").value;
        renderResult("kb-result", { pending: true });
        call("POST", "/api/kb", { title: title, content: content, tags: tags })
            .then(markNotImplemented)
            .then(function (p) { renderResult("kb-result", p); });
    }

    function kbGet() {
        var id = el("kb-id").value;
        if (!id) {
            renderResult("kb-result", { ok: false, error: { code: "validation", message: "Введите id" } });
            return;
        }
        renderResult("kb-result", { pending: true });
        call("GET", "/api/kb/" + id)
            .then(markNotImplemented)
            .then(function (p) { renderResult("kb-result", p); });
    }

    function kbUpdate() {
        var id = el("kb-id").value;
        if (!id) {
            renderResult("kb-result", { ok: false, error: { code: "validation", message: "Введите id" } });
            return;
        }
        var title = el("kb-title").value;
        if (!title) {
            renderResult("kb-result", { ok: false, error: { code: "validation", message: "Введите заголовок" } });
            return;
        }
        var tags = el("kb-tags").value
            .split(",")
            .map(function (t) { return t.trim(); })
            .filter(Boolean);
        var content = el("kb-content").value;
        renderResult("kb-result", { pending: true });
        call("PUT", "/api/kb/" + id, { title: title, content: content, tags: tags })
            .then(markNotImplemented)
            .then(function (p) { renderResult("kb-result", p); });
    }

    function kbDelete() {
        var id = el("kb-id").value;
        if (!id) {
            renderResult("kb-result", { ok: false, error: { code: "validation", message: "Введите id" } });
            return;
        }
        renderResult("kb-result", { pending: true });
        call("DELETE", "/api/kb/" + id)
            .then(markNotImplemented)
            .then(function (p) { renderResult("kb-result", p); });
    }

    function dashboard() {
        renderResult("metrics-result", { pending: true });
        call("GET", "/api/dashboard").then(function (p) { renderResult("metrics-result", p); });
    }

    function logs() {
        renderResult("metrics-result", { pending: true });
        call("GET", "/api/logs").then(function (p) { renderResult("metrics-result", p); });
    }

    function escalations() {
        renderResult("metrics-result", { pending: true });
        call("GET", "/api/escalations").then(function (p) { renderResult("metrics-result", p); });
    }

    function settingsGet() {
        renderResult("settings-result", { pending: true });
        call("GET", "/api/settings").then(function (p) { renderResult("settings-result", p); });
    }

    function settingsPut() {
        var body = {};
        var threshold = el("settings-threshold").value;
        if (threshold !== "") body.confidence_threshold = parseInt(threshold, 10);
        var strategy = el("settings-strategy").value;
        if (strategy) body.escalation_strategy = strategy;
        renderResult("settings-result", { pending: true });
        call("PUT", "/api/settings", body).then(function (p) { renderResult("settings-result", p); });
    }

    function intList() {
        renderResult("integrations-result", { pending: true });
        call("GET", "/api/integrations").then(function (p) { renderResult("integrations-result", p); });
    }

    function bitrixWebhook() {
        var body = {};
        var webhook = el("bitrix-webhook").value;
        var chat = el("bitrix-chat").value;
        if (!webhook) {
            renderResult("integrations-result", { ok: false, error: { code: "validation", message: "Введите webhook_url" } });
            return;
        }
        body.webhook_url = webhook;
        if (chat) body.chat_id = chat;
        renderResult("integrations-result", { pending: true });
        call("POST", "/api/integrations/bitrix/webhook", body)
            .then(markNotImplemented)
            .then(function (p) { renderResult("integrations-result", p); });
    }

    function redmineWebhook() {
        var url = el("redmine-url").value;
        var key = el("redmine-key").value;
        if (!url || !key) {
            renderResult("integrations-result", { ok: false, error: { code: "validation", message: "Введите url и api_key" } });
            return;
        }
        var body = { url: url, api_key: key };
        var project = el("redmine-project").value;
        if (project) body.project_id = project;
        renderResult("integrations-result", { pending: true });
        call("POST", "/api/integrations/redmine/webhook", body)
            .then(markNotImplemented)
            .then(function (p) { renderResult("integrations-result", p); });
    }

    var actions = {
        chat: submitChat,
        image: submitImage,
        "kb-list": kbList,
        "kb-create": kbCreate,
        "kb-get": kbGet,
        "kb-update": kbUpdate,
        "kb-delete": kbDelete,
        dashboard: dashboard,
        logs: logs,
        escalations: escalations,
        "settings-get": settingsGet,
        "settings-put": settingsPut,
        "int-list": intList,
        "bitrix-webhook": bitrixWebhook,
        "redmine-webhook": redmineWebhook,
    };

    document.addEventListener("DOMContentLoaded", function () {
        document.querySelectorAll("[data-action]").forEach(function (btn) {
            btn.addEventListener("click", function () {
                var handler = actions[btn.getAttribute("data-action")];
                if (handler) handler();
            });
        });
    });
})();