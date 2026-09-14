        const themeToggleBtn = document.getElementById('themeToggleBtn');
        const themeIcon = document.getElementById('themeIcon');
        
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            if (document.body.classList.contains('light-theme')) {
                themeIcon.classList.remove('fa-moon');
                themeIcon.classList.add('fa-sun');
            } else {
                themeIcon.classList.remove('fa-sun');
                themeIcon.classList.add('fa-moon');
            }
        });

        const navItems = document.querySelectorAll('.nav-menu li[data-tab]');
        const tabContents = document.querySelectorAll('.tab-content');

        function switchTab(tabId) {
            navItems.forEach(nav => {
                if (nav.getAttribute('data-tab') === tabId) {
                    nav.classList.add('active');
                } else {
                    nav.classList.remove('active');
                }
            });

            tabContents.forEach(tab => {
                if (tab.id === 'tab-' + tabId) {
                    tab.classList.add('active');
                } else {
                    tab.classList.remove('active');
                }
            });

            loadTabData(tabId);
        }

        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const targetTab = item.getAttribute('data-tab');
                switchTab(targetTab);
            });
        });

        // Переключение выпадающего списка уведомлений
        const notificationBtn = document.getElementById('notificationBtn');
        const notificationPopup = document.getElementById('notificationPopup');
        
        notificationBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            notificationPopup.classList.toggle('active');
        });

        document.addEventListener('click', (e) => {
            if (!notificationPopup.contains(e.target) && e.target !== notificationBtn) {
                notificationPopup.classList.remove('active');
            }
        });

        document.getElementById('clearNotifications').addEventListener('click', () => {
            document.querySelector('.badge-dot').style.display = 'none';
            showToast('Все уведомления помечены как прочитанные');
            notificationPopup.classList.remove('active');
        });

        /* РЕДАКТИРОВАНИЕ ПРОФИЛЯ */
        function openProfileModal() {
            document.getElementById('profileModal').classList.add('active');
        }

        function closeProfileModal() {
            document.getElementById('profileModal').classList.remove('active');
        }

        function handleAvatarUpload(input) {
            if (input.files && input.files[0]) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    document.getElementById('avatarPreviewModal').src = e.target.result;
                }
                reader.readAsDataURL(input.files[0]);
            }
        }

        function saveProfileChanges() {
            const name = document.getElementById('editProfileName').value;
            const role = document.getElementById('editProfileRole').value;
            const avatarSrc = document.getElementById('avatarPreviewModal').src;

            document.getElementById('userProfileName').innerText = name;
            document.getElementById('userProfileRole').innerText = role;
            document.getElementById('userAvatarImg').src = avatarSrc;

            closeProfileModal();
            showToast('Профиль успешно обновлен!');
        }

        /* СОХРАНЕНИЕ И ЭКСПОРТ ЛОГОВ */
        function saveLogsHistory() {
            const table = document.getElementById('logsTable');
            let rows = [];
            for (let i = 0; i < table.rows.length; i++) {
                let row = [], cols = table.rows[i].querySelectorAll('td, th');
                for (let j = 0; j < cols.length; j++) {
                    row.push(cols[j].innerText.replace(/\n/g, ' '));
                }
                rows.push(row.join('\t'));
            }
            const logsText = rows.join('\n');
            const blob = new Blob([logsText], { type: 'text/plain;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `logs_history_${new Date().toISOString().slice(0,10)}.txt`;
            link.click();
            showToast('История логов успешно сохранена в файл!');
        }

        function exportLogsCSV() {
            const table = document.getElementById('logsTable');
            let rows = [];
            for (let i = 0; i < table.rows.length; i++) {
                let row = [], cols = table.rows[i].querySelectorAll('td, th');
                for (let j = 0; j < cols.length; j++) {
                    row.push('"' + cols[j].innerText.replace(/"/g, '""').replace(/\n/g, ' ') + '"');
                }
                rows.push(row.join(','));
            }
            const csvContent = '\uFEFF' + rows.join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = `logs_report_${new Date().toISOString().slice(0,10)}.csv`;
            link.click();
            showToast('Отчет экспортирован в CSV!');
        }

        function updateConfidenceSlider(val) {
            document.getElementById('confidenceValBadge').innerText = val + '%';
            const statusText = document.getElementById('sliderStatusText');
            
            if (val < 40) {
                statusText.innerText = 'Режим: Низкий порог (ИИ отвечает часто)';
                statusText.style.color = 'var(--accent-red)';
            } else if (val <= 75) {
                statusText.innerText = `Режим: Сбалансированный авто-ответ (${val}%+)`;
                statusText.style.color = 'var(--accent-cyan)';
            } else {
                statusText.innerText = `Режим: Строгий (Уверенность > ${val}%)`;
                statusText.style.color = 'var(--accent-orange)';
            }
        }

        function saveAgentSettings() {
            const threshold = parseInt(document.getElementById('confidenceRange').value, 10);
            const strategy = document.getElementById('escalationStrategy').value;
            const body = {
                confidence_threshold: threshold,
                escalation_strategy: strategy === 'Автоматическая эскалация в Redmine / Bitrix24' ? 'escalation' : 'clarify'
            };
            API.settingsPut(body).then((res) => {
                if (res.ok) {
                    showToast('Настройки агента АО "Молвест" успешно сохранены');
                } else {
                    showToast('Ошибка сохранения: ' + API.errorMessage(res));
                }
            });
        }

        /* ПОЛЬЗОВАТЕЛИ И МОДАЛЬНОЕ ОКНО */
        let currentEditRow = null;

        function openAddUserModal() {
            currentEditRow = null;
            document.getElementById('modalUserTitle').innerText = 'Добавление нового пользователя';
            document.getElementById('inputUserName').value = '';
            document.getElementById('inputUserEmail').value = '';
            document.getElementById('userRoleModal').classList.add('active');
        }

        function editUserRow(btn) {
            currentEditRow = btn.closest('tr');
            const name = currentEditRow.cells[0].querySelector('strong').innerText;
            const email = currentEditRow.cells[0].querySelector('div').innerText;
            const dept = currentEditRow.cells[1].innerText;

            document.getElementById('modalUserTitle').innerText = 'Редактирование профиля';
            document.getElementById('inputUserName').value = name;
            document.getElementById('inputUserEmail').value = email;
            document.getElementById('inputUserDept').value = dept;
            document.getElementById('userRoleModal').classList.add('active');
        }

        function saveUserForm() {
            const name = document.getElementById('inputUserName').value.trim();
            const email = document.getElementById('inputUserEmail').value.trim();
            const dept = document.getElementById('inputUserDept').value;
            const role = document.getElementById('inputUserRole').value;

            if (!name || !email) {
                showToast('Заполните обязательные поля!');
                return;
            }

            let dbs = [];
            if(document.getElementById('dbErp').checked) dbs.push('<span class="badge-status badge-blue">ERP</span>');
            if(document.getElementById('dbZup').checked) dbs.push('<span class="badge-status badge-blue">ЗУП</span>');
            if(document.getElementById('dbUt').checked) dbs.push('<span class="badge-status badge-blue">УТ</span>');
            if(document.getElementById('dbBp').checked) dbs.push('<span class="badge-status badge-blue">БП</span>');
            const dbHTML = dbs.join(' ');

            if (currentEditRow) {
                currentEditRow.cells[0].innerHTML = `<strong>${name}</strong><div style="font-size: 11px; color: var(--text-muted);">${email}</div>`;
                currentEditRow.cells[1].innerText = dept;
                currentEditRow.cells[2].innerHTML = `<span class="badge-status badge-warning">${role}</span>`;
                currentEditRow.cells[3].innerHTML = dbHTML;
                showToast('Данные пользователя обновлены');
            } else {
                const table = document.getElementById('usersTable').getElementsByTagName('tbody')[0];
                const newRow = table.insertRow(0);
                newRow.innerHTML = `
                    <td><strong>${name}</strong><div style="font-size: 11px; color: var(--text-muted);">${email}</div></td>
                    <td>${dept}</td>
                    <td><span class="badge-status badge-warning">${role}</span></td>
                    <td>${dbHTML}</td>
                    <td><span class="badge-status badge-success">Активен</span></td>
                    <td>
                        <button class="btn-action-icon" title="Редактировать" onclick="editUserRow(this)"><i class="fa-solid fa-pen-to-square"></i></button>
                        <button class="btn-action-icon danger" title="Заблокировать" onclick="deleteUserRow(this)"><i class="fa-solid fa-user-xmark"></i></button>
                    </td>
                `;
                showToast('Новый пользователь успешно добавлен!');
            }

            closeUserModal();
        }

        function deleteUserRow(btn) {
            if (confirm('Вы уверены, что хотите деактивировать доступ пользователя?')) {
                const row = btn.closest('tr');
                row.remove();
                showToast('Пользователь деактивирован');
            }
        }

        function closeUserModal() {
            document.getElementById('userRoleModal').classList.remove('active');
        }

        function removeKbFile(btn) {
            const item = btn.closest('.file-item');
            const docId = btn.getAttribute('data-doc-id');
            if (!item) return;
            if (docId) {
                if (!confirm('Удалить документ из базы знаний?')) return;
                API.kbDelete(docId).then((res) => {
                    if (res.ok) {
                        showToast('Документ удален из базы знаний');
                        loadKb();
                    } else {
                        showToast('Ошибка удаления: ' + API.errorMessage(res));
                    }
                });
            } else {
                item.remove();
                showToast('Файл удален из базы знаний');
            }
        }

        function showToast(message) {
            const toast = document.getElementById('toastNotification');
            const toastText = document.getElementById('toastText');
            toastText.innerText = message;
            toast.classList.add('show');
            setTimeout(() => { toast.classList.remove('show'); }, 3000);
        }

        function filterOverviewData(type, element) {
            document.querySelectorAll('.metric-card').forEach(c => c.classList.remove('active-filter'));
            element.classList.add('active-filter');
            showToast('Фильтр метрик обновлен');
        }

        function updateChartTimeframe(tf, btn) {
            document.querySelectorAll('.btn-timeframe').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            showToast('Интервал обновлен');
        }

        function triggerFileInput(id) { document.getElementById(id).click(); }

        function handleKbUpload(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                API.kbUpload(file).then((res) => {
                    if (res.ok && res.data && res.data.accepted) {
                        showToast(`Файл "${file.name}" загружен и проиндексирован`);
                        loadKb();
                    } else {
                        showToast('Ошибка загрузки: ' + API.errorMessage(res));
                    }
                });
            }
        }

        function handleScreenshotUpload(input) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                const box = document.getElementById('screenshotResult');
                box.innerHTML = '<div class="ai-thinking-indicator"><i class="fa-solid fa-spinner fa-spin"></i><span>AI-Агент анализирует скриншот...</span></div>';
                API.chatImage(file).then((res) => {
                    if (res.ok && res.data && res.data.analysis) {
                        box.innerHTML = '<div class="feedback-item"><div class="feedback-header"><strong>Результат анализа</strong></div><div class="feedback-text">' + escapeHtml(res.data.analysis) + '</div></div>';
                        showToast(`Скриншот "${file.name}" проанализирован`);
                    } else if (res.ok && res.data && res.data.error) {
                        box.innerHTML = '<div class="ai-thinking-indicator" style="color: var(--accent-red); border-color: var(--accent-red);"><i class="fa-solid fa-triangle-exclamation"></i><span>' + escapeHtml(res.data.error) + '</span></div>';
                    } else {
                        box.innerHTML = '<div class="ai-thinking-indicator" style="color: var(--accent-red); border-color: var(--accent-red);"><i class="fa-solid fa-triangle-exclamation"></i><span>' + API.errorMessage(res) + '</span></div>';
                    }
                });
            }
        }

        /* LIVE CHAT TAKEOVER & AI ACCOUNTING LOGIC */
        let isChatTakenOver = false;

        function takeoverChat() {
            isChatTakenOver = true;
            
            // Update banner appearance & message
            const banner = document.getElementById('liveObserverBanner');
            banner.style.background = 'rgba(255, 209, 102, 0.12)';
            banner.style.borderColor = 'var(--accent-orange)';
            document.getElementById('liveBannerText').innerHTML = `
                <i class="fa-solid fa-headset" style="color: var(--accent-orange);"></i> <strong>Ручное управление:</strong> Диалог перехвачен. <strong>AI учитывает ответы оператора</strong> и подстраивает подсказки.
            `;
            
            const takeoverBtn = document.getElementById('takeoverBtn');
            takeoverBtn.innerHTML = '<i class="fa-solid fa-robot"></i> Вернуть AI';
            takeoverBtn.style.background = 'var(--accent-blue)';
            takeoverBtn.setAttribute('onclick', 'returnChatToAI()');

            // Enable input area in live chat
            const inputArea = document.getElementById('liveChatInputArea');
            inputArea.style.opacity = '1';
            const inputField = document.getElementById('liveChatInputField');
            inputField.disabled = false;
            inputField.placeholder = 'Введите ответ оператора клиенту...';
            
            const sendBtn = document.getElementById('liveChatSendBtn');
            sendBtn.disabled = false;
            sendBtn.style.background = 'var(--accent-blue)';
            sendBtn.style.cursor = 'pointer';
            sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Отправить';

            // AI reports about takeover in the chat history
            const history = document.getElementById('liveChatHistory');
            const aiNotice = document.createElement('div');
            aiNotice.className = 'msg msg-ai';
            aiNotice.style.borderLeft = '3px solid var(--accent-orange)';
            aiNotice.innerHTML = '<i class="fa-solid fa-robot"></i> <strong>AI-Агент:</strong> Диалог успешно перехвачен оператором. Я перешел в режим ассистента: учитываю ваши ответы, фиксирую историю взаимодействия и продолжаю фоновый мониторинг.';
            history.appendChild(aiNotice);
            history.scrollTop = history.scrollHeight;

            showToast('Диалог перехвачен! AI учитывает ваши ответы.');
        }

        function returnChatToAI() {
            isChatTakenOver = false;
            
            const banner = document.getElementById('liveObserverBanner');
            banner.style.background = 'rgba(6, 214, 160, 0.08)';
            banner.style.borderColor = 'var(--accent-cyan)';
            document.getElementById('liveBannerText').innerHTML = `
                <i class="fa-solid fa-eye"></i> <strong>Режим наблюдения:</strong> Вы просматриваете диалог в реальном времени. AI отвечает автоматически.
            `;
            
            const takeoverBtn = document.getElementById('takeoverBtn');
            takeoverBtn.innerHTML = '<i class="fa-solid fa-hand"></i> Перехватить диалог';
            takeoverBtn.style.background = 'var(--accent-orange)';
            takeoverBtn.setAttribute('onclick', 'takeoverChat()');

            const inputArea = document.getElementById('liveChatInputArea');
            inputArea.style.opacity = '0.7';
            const inputField = document.getElementById('liveChatInputField');
            inputField.disabled = true;
            inputField.placeholder = 'Режим наблюдения активен...';
            
            const sendBtn = document.getElementById('liveChatSendBtn');
            sendBtn.disabled = true;
            sendBtn.style.background = 'var(--text-muted)';
            sendBtn.style.cursor = 'not-allowed';
            sendBtn.innerHTML = '<i class="fa-solid fa-lock"></i> Наблюдение';

            const history = document.getElementById('liveChatHistory');
            const aiNotice = document.createElement('div');
            aiNotice.className = 'msg msg-ai';
            aiNotice.style.borderLeft = '3px solid var(--accent-cyan)';
            aiNotice.innerHTML = '<i class="fa-solid fa-robot"></i> <strong>AI-Агент:</strong> Автоматическое управление возобновлено.';
            history.appendChild(aiNotice);
            history.scrollTop = history.scrollHeight;

            showToast('Управление возвращено AI-агенту');
        }

        function sendLiveOperatorMessage() {
            const inputField = document.getElementById('liveChatInputField');
            const text = inputField.value.trim();
            if (!text) return;

            const history = document.getElementById('liveChatHistory');

            const opMsg = document.createElement('div');
            opMsg.className = 'msg msg-user';
            opMsg.style.background = 'var(--accent-orange)';
            opMsg.innerHTML = `<strong>Оператор:</strong> ${text}`;
            history.appendChild(opMsg);

            inputField.value = '';
            history.scrollTop = history.scrollHeight;

            API.chat(text).then((res) => {
                const aiResponse = document.createElement('div');
                aiResponse.className = 'msg msg-ai';
                aiResponse.style.borderLeft = '3px solid var(--accent-cyan)';
                if (isNotImplemented(res)) {
                    aiResponse.innerHTML = `<i class="fa-solid fa-robot"></i> <strong>AI-Агент:</strong> Подсказка скоро будет доступна (статус not_implemented).`;
                } else if (res.ok && res.data) {
                    const apiResponse = res.data;
                    aiResponse.innerHTML = `<i class="fa-solid fa-robot"></i> <strong>AI-Агент:</strong> ${apiResponse.answer || ''} <span class="badge-status badge-success" style="margin-left:6px;">${apiResponse.confidence || 0}%</span>`;
                } else {
                    aiResponse.innerHTML = `<i class="fa-solid fa-robot"></i> <strong>AI-Агент:</strong> ${API.errorMessage(res)}`;
                }
                history.appendChild(aiResponse);
                history.scrollTop = history.scrollHeight;
            });
        }

        function sendChatMessage() {
            const inputField = document.getElementById('chatInput');
            const text = inputField.value.trim();
            if (!text) return;

            const history = document.getElementById('chatHistory');
            const opMsg = document.createElement('div');
            opMsg.className = 'msg msg-user';
            opMsg.innerHTML = text;
            history.appendChild(opMsg);
            inputField.value = '';
            history.scrollTop = history.scrollHeight;

            API.chat(text).then((res) => {
                const aiResponse = document.createElement('div');
                aiResponse.className = 'msg msg-ai';
                aiResponse.style.borderLeft = '3px solid var(--accent-cyan)';
                if (isNotImplemented(res)) {
                    aiResponse.innerHTML = '<i class="fa-solid fa-robot"></i> <strong>AI-Агент:</strong> Ответ доступен после подключения ядра (not_implemented).';
                } else if (res.ok && res.data) {
                    aiResponse.innerHTML = `<i class="fa-solid fa-robot"></i> <strong>AI-Агент:</strong> ${res.data.answer || ''} <span class="badge-status badge-success" style="margin-left:6px;">${res.data.confidence || 0}%</span>`;
                } else {
                    aiResponse.innerHTML = `<i class="fa-solid fa-robot"></i> <strong>AI-Агент:</strong> ${API.errorMessage(res)}`;
                }
                history.appendChild(aiResponse);
                history.scrollTop = history.scrollHeight;
            });
        }

        function selectLiveChat(element, user, topic, confidence) {
            document.querySelectorAll('#tab-live-chats .chat-item').forEach(c => c.classList.remove('active'));
            element.classList.add('active');
            if (user) document.getElementById('liveUserTitle').innerText = user;
            if (topic) {
                document.getElementById('liveTopic').innerHTML = `<i class="fa-solid fa-robot"></i> Тема: ${topic} • Точность модели: <strong style="color: var(--accent-cyan);" id="liveConfidence">${confidence || ''}</strong>`;
            }
        }

        function selectChat(element, user) {
            document.querySelectorAll('#tab-chats .chat-item').forEach(c => c.classList.remove('active'));
            element.classList.add('active');
            if (user) document.getElementById('currentChatUser').innerText = user;
        }

        /* API-ИНТЕГРАЦИЯ ПАНЕЛИ */
        function isNotImplemented(payload) {
            return payload && payload.ok && payload.data &&
                typeof payload.data.status === 'string' &&
                payload.data.status.indexOf('not_implemented') !== -1;
        }

        function escapeHtml(value) {
            return String(value == null ? '' : value)
                .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }

        function strategyToLabel(strategy) {
            if (!strategy) return '';
            if (strategy === 'clarify') return 'Запросить уточнение у сотрудника';
            if (strategy === 'operator') return 'Перевести на живого оператора в чат';
            return 'Автоматическая эскалация в Redmine / Bitrix24';
        }

        function strategyToKey(label) {
            if (label === 'Запросить уточнение у сотрудника') return 'clarify';
            if (label === 'Перевести на живого оператора в чат') return 'operator';
            return 'human_review';
        }

        function statusBadge(status) {
            const lower = String(status || '').toLowerCase();
            if (lower.indexOf('success') !== -1 || lower.indexOf('resolved') !== -1) return '<span class="badge-status badge-success">Успешно</span>';
            if (lower.indexOf('escalat') !== -1 || lower.indexOf('escalated') !== -1) return '<span class="badge-status badge-warning">Эскалировано</span>';
            if (lower.indexOf('error') !== -1 || lower.indexOf('not_implemented') !== -1) return '<span class="badge-status badge-warning">В разработке</span>';
            return '<span class="badge-status badge-blue">' + escapeHtml(status || '—') + '</span>';
        }

        function confidenceBadge(confidence) {
            const c = parseInt(confidence, 10);
            if (isNaN(c)) return '<strong>—</strong>';
            if (c >= 75) return '<strong>' + c + '%</strong>';
            if (c >= 40) return '<strong style="color: var(--accent-orange);">' + c + '%</strong>';
            return '<strong style="color: var(--accent-red);">' + c + '%</strong>';
        }

        function loadDashboard() {
            API.dashboard().then((res) => {
                if (!res.ok) {
                    showToast('Ошибка метрик: ' + API.errorMessage(res));
                    return;
                }
                const data = res.data || {};
                const totalEl = document.getElementById('metricTotal');
                const autoEl = document.getElementById('metricAutoSolve');
                const avgEl = document.getElementById('metricAvgMs');
                if (totalEl) totalEl.innerText = (data.total_requests || 0) > 0 ? data.total_requests.toLocaleString('ru-RU') : '—';
                if (autoEl) autoEl.innerText = data.success_rate > 0 ? data.success_rate + '%' : '—';
                if (avgEl) avgEl.innerText = (data.avg_response_ms || 0) > 0 ? (data.avg_response_ms / 1000).toFixed(1) + ' сек' : '—';
            });
        }

        function loadSettings() {
            API.settingsGet().then((res) => {
                if (!res.ok) return;
                const data = res.data || {};
                const range = document.getElementById('confidenceRange');
                if (range && typeof data.confidence_threshold === 'number') {
                    range.value = data.confidence_threshold;
                    updateConfidenceSlider(range.value);
                }
                const select = document.getElementById('escalationStrategy');
                if (select) {
                    const label = strategyToLabel(data.escalation_strategy);
                    [...select.options].forEach((o) => { o.selected = (o.text === label); });
                }
            });
        }

        function loadKb() {
            API.kbList().then((res) => {
                const list = document.getElementById('kbFileList');
                const counter = document.getElementById('kbCountText');
                if (!res.ok) {
                    if (list) list.innerHTML = '';
                    if (counter) counter.innerText = 'Подключенные файлы базы знаний';
                    showToast('Ошибка базы знаний: ' + API.errorMessage(res));
                    return;
                }
                const items = res.data && res.data.items ? res.data.items : [];
                if (counter) counter.innerText = 'Подключенные файлы базы знаний (' + items.length + ')';
                if (!list) return;
                list.innerHTML = items.length
                    ? items.map((doc) => {
                        const name = doc.title || 'Без названия';
                        const ext = (name.split('.').pop() || '').toLowerCase();
                        const icon = ext === 'pdf' ? 'fa-file-pdf' : (ext === 'docx' || ext === 'doc') ? 'fa-file-word' : (ext === 'db') ? 'fa-server' : 'fa-file-lines';
                        const meta = 'id=' + (doc.id || '—') + ' • Статус: ' + (doc.status || '—') + (doc.source_file ? ' • ' + doc.source_file : '');
                        const badge = doc.indexed
                            ? '<span class="badge-status badge-success">Индексирован</span>'
                            : '<span class="badge-status badge-warning">Без индекса</span>';
                        return '<div class="file-item">' +
                            '<div class="file-info"><i class="fa-solid ' + icon + '"></i><div><div>' + escapeHtml(name) + '</div><div class="file-meta">' + escapeHtml(meta) + '</div></div></div>' +
                            '<div class="file-actions">' + badge +
                            '<button class="btn-action-icon danger" title="Удалить" data-doc-id="' + (doc.id || '') + '" onclick="removeKbFile(this)"><i class="fa-solid fa-trash"></i></button></div></div>';
                    }).join('')
                    : '<div class="feedback-item"><div class="feedback-text">Документы еще не загружены. Добавьте первый файл через кнопку «Загрузить новый файл».</div></div>';
            });
        }

        function loadLogs() {
            API.logs().then((res) => {
                const tbody = document.querySelector('#logsTable tbody');
                if (!tbody) return;
                if (!res.ok || !res.data || !res.data.items || !res.data.items.length) {
                    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color: var(--text-muted);">Журнал пуст. Записи появятся после подключения ядра.</td></tr>';
                    return;
                }
                tbody.innerHTML = res.data.items.map((it) => {
                    const badge = it.confidence != null ? confidenceBadge(it.confidence) : '<strong>—</strong>';
                    return '<tr>' +
                        '<td>' + escapeHtml(it.created_at || it.time || '—') + '</td>' +
                        '<td>' + escapeHtml(it.channel || '—') + '</td>' +
                        '<td>' + escapeHtml(it.query || it.question || '—') + '</td>' +
                        '<td>' + badge + '</td>' +
                        '<td>' + statusBadge(it.status) + '</td></tr>';
                }).join('');
            });
        }

        function loadEscalations() {
            API.escalations().then((res) => {
                const items = res.ok && res.data && res.data.items ? res.data.items : [];
                const badge = document.getElementById('liveChatBadge');
                if (badge) badge.innerText = items.length || '0';
                const dot = document.querySelector('.badge-dot');
                if (dot) dot.style.display = items.length ? 'block' : 'none';
                const popup = document.getElementById('notificationPopup');
                if (!popup) return;
                popup.querySelectorAll('.dropdown-item').forEach((n) => n.remove());
                const wrap = document.createElement('div');
                if (items.length) {
                    wrap.innerHTML = items.map((it) =>
                        '<div class="dropdown-item"><strong><i class="fa-solid fa-triangle-exclamation" style="color: var(--accent-orange); margin-right: 4px;"></i> Эскалация</strong>' +
                        '<p>' + escapeHtml(it.question || 'Запрос') + '</p>' +
                        '<span style="font-size: 10px; color: var(--text-muted); font-style: italic;">Уверенность: ' + (it.confidence != null ? it.confidence + '%' : '—') + ' • ' + escapeHtml(it.status || '') + '</span></div>'
                    ).join('');
                } else {
                    wrap.innerHTML = '<div class="dropdown-item"><strong>Нет активных эскалаций</strong><p>Все обращения обработаны автоматически.</p></div>';
                }
                popup.appendChild(wrap);
            });
        }

        function loadTabData(tabId) {
            if (tabId === 'overview') loadDashboard();
            else if (tabId === 'settings') loadSettings();
            else if (tabId === 'kb') loadKb();
            else if (tabId === 'logs') loadLogs();
            else if (tabId === 'live-chats') loadEscalations();
        }

        function refreshActiveTab() {
            const activeNav = document.querySelector('.nav-menu li[data-tab].active');
            if (activeNav) loadTabData(activeNav.getAttribute('data-tab'));
        }

        refreshActiveTab();
        loadEscalations();