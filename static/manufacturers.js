/* Shared central directory UI: no part associations and no additional storage keys. */
(function () {
    'use strict';
    const words = {
        en: { title: 'Manufacturer directory', back: 'BOM dashboard', create: 'New manufacturer', edit: 'Edit', save: 'Save', cancel: 'Cancel', close: 'Close', name: 'Name', address: 'Address', notes: 'Notes', phones: 'Phones', emails: 'Emails', socials: 'Social accounts', platform: 'Platform', handle: 'Handle', active: 'Active', inactive: 'Inactive', all: 'All statuses', search: 'Search name, contacts or notes', tags: 'Tags', categories: 'Categories', category: 'Category', anyCategory: 'All categories', noCategory: 'Uncategorized', add: 'Add', remove: 'Remove', loading: 'Loading…', retry: 'Retry', failed: 'Request failed. Check your connection, sign-in and API availability.', empty: 'No manufacturers match these filters.', filtered: 'Export filtered Excel', exportAll: 'Export all Excel', exportOne: 'Excel', taxonomy: 'Manage categories & tags', rename: 'Rename', suggestions: 'Suggestions (not created automatically): Machining, Casting, Sheet metal, Assembly, Finishing', tagHint: 'Selected tags are combined with AND. Categories and tags are user-defined.', nameRequired: 'Name is required.', phone: 'Phone', email: 'Email', used: 'Saved in the central directory; not attached to a part.', unavailable: 'Directory metadata is unavailable. Retry before editing tags.', count: 'Matching manufacturers', newCategory: 'New category', newTag: 'New tag', invalid: 'Unexpected API response', saving: 'Saving…' },
        fa: { title: 'دفتر مرکزی سازندگان', back: 'داشبورد BOM', create: 'سازنده جدید', edit: 'ویرایش', save: 'ذخیره', cancel: 'انصراف', close: 'بستن', name: 'نام', address: 'آدرس', notes: 'یادداشت', phones: 'تلفن‌ها', emails: 'ایمیل‌ها', socials: 'شبکه‌های اجتماعی', platform: 'پلتفرم', handle: 'شناسه', active: 'فعال', inactive: 'غیرفعال', all: 'همه وضعیت‌ها', search: 'جستجوی نام، اطلاعات تماس یا یادداشت', tags: 'برچسب‌ها', categories: 'دسته‌ها', category: 'دسته', anyCategory: 'همه دسته‌ها', noCategory: 'بدون دسته', add: 'افزودن', remove: 'حذف', loading: 'در حال بارگذاری…', retry: 'تلاش مجدد', failed: 'درخواست ناموفق بود. اتصال، ورود به حساب و دسترسی API را بررسی کنید.', empty: 'سازنده‌ای مطابق فیلترها یافت نشد.', filtered: 'Excel نتایج فیلترشده', exportAll: 'Excel همه سازندگان', exportOne: 'Excel', taxonomy: 'مدیریت دسته‌ها و برچسب‌ها', rename: 'تغییر نام', suggestions: 'پیشنهادها (خودکار ایجاد نمی‌شوند): ماشین‌کاری، ریخته‌گری، ورق‌کاری، مونتاژ، پرداخت', tagHint: 'برچسب‌های انتخاب‌شده با شرط «و» ترکیب می‌شوند. دسته‌ها و برچسب‌ها قابل تعریف هستند.', nameRequired: 'نام الزامی است.', phone: 'تلفن', email: 'ایمیل', used: 'در دفتر مرکزی ذخیره شد؛ به قطعه متصل نشده است.', unavailable: 'اطلاعات دسته‌ها و برچسب‌ها در دسترس نیست. پیش از ویرایش برچسب‌ها دوباره تلاش کنید.', count: 'سازندگان مطابق فیلتر', newCategory: 'دسته جدید', newTag: 'برچسب جدید', invalid: 'پاسخ API نامعتبر است', saving: 'در حال ذخیره…' }
    };
    Object.assign(words.en, { selectCategory: 'Select a category', categoryRequired: 'Choose an existing category. Create a category first if none exist.', deleteDefinition: 'Delete', confirmDelete: 'Delete this definition?', definitionInUse: 'This category or tag is in use and cannot be deleted. No associations were removed.' });
    Object.assign(words.fa, { selectCategory: 'انتخاب دسته', categoryRequired: 'یک دسته موجود را انتخاب کنید. اگر دسته‌ای وجود ندارد، ابتدا دسته ایجاد کنید.', deleteDefinition: 'حذف', confirmDelete: 'این دسته یا برچسب حذف شود؟', definitionInUse: 'این دسته یا برچسب در حال استفاده است و قابل حذف نیست. هیچ ارتباطی حذف نشد.' });
    function lang() { return window.currentLang === 'en' || document.documentElement.lang === 'en' ? 'en' : 'fa'; }
    function tr(key) { return words[lang()][key] || key; }
    function esc(value) { return String(value == null ? '' : value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
    function button(label, action, className) {
        const b = document.createElement('button'); b.type = 'button'; b.textContent = label;
        b.className = className || 'mfg-button'; b.addEventListener('click', action); return b;
    }
    async function request(path, options) {
        const response = await fetch('/api/v2' + path, options);
        const result = await response.json().catch(() => null);
        if (!response.ok) {
            const error = new Error(response.status === 409 && options && options.method === 'DELETE'
                ? tr('definitionInUse') : (result && result.error || 'HTTP ' + response.status));
            error.status = response.status; throw error;
        }
        const deleting = options && options.method === 'DELETE';
        if (!result || result.success !== true || (!deleting && !Object.prototype.hasOwnProperty.call(result, 'data'))) throw new Error(result && result.error || tr('invalid'));
        return result.data;
    }
    async function list(path) { const data = await request(path); if (!Array.isArray(data)) throw new Error(tr('invalid')); return data; }
    function query(filters) {
        const p = new URLSearchParams(); p.set('active', filters.active || 'all');
        if (filters.q && filters.q.trim()) p.set('q', filters.q.trim());
        if (filters.category_id) p.set('category_id', filters.category_id);
        (filters.tag_ids || []).forEach(id => p.append('tag_id', id));
        return p.toString();
    }
    function isActive(m) { return m.is_active !== false && m.is_active !== 0; }
    function contacts(m) {
        const phones = Array.isArray(m.phones) ? m.phones.map(p => p.phone) : [];
        if (m.phone && !phones.includes(m.phone)) phones.unshift(m.phone);
        return [...phones, ...(m.emails || []).map(e => e.email), ...(m.socials || []).map(s => [s.platform, s.handle].filter(Boolean).join(': '))].filter(Boolean);
    }
    function summary(m) {
        return `<div class="mfg-contact" dir="auto">${contacts(m).map(esc).join(' · ')}</div><div class="mfg-tags">${(m.tags || []).map(tag => `<span class="mfg-chip">${esc(tag.category_name ? tag.category_name + ': ' : '')}${esc(tag.name)}</span>`).join('')}</div>`;
    }
    async function exportExcel(path) {
        const response = await fetch('/api/v2' + path);
        if (!response.ok) throw new Error('HTTP ' + response.status);
        const type = response.headers.get('content-type') || '';
        if (/json|html/i.test(type)) throw new Error(tr('invalid'));
        const blob = await response.blob(); if (!blob.size) throw new Error(tr('invalid'));
        const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url;
        a.download = 'manufacturers.xlsx'; document.body.append(a); a.click(); a.remove();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    }
    function errorMessage(element, error, retry) {
        element.replaceChildren(); element.className = 'mfg-message mfg-error'; element.setAttribute('role', 'alert');
        const p = document.createElement('p'); p.textContent = error.status === 409 ? error.message : tr('failed') + ' ' + error.message; element.append(p);
        if (retry) element.append(button(tr('retry'), retry));
    }
    function modal(title) {
        const overlay = document.createElement('div'); overlay.className = 'mfg-overlay';
        const card = document.createElement('section'); card.className = 'mfg-modal'; card.setAttribute('role', 'dialog'); card.setAttribute('aria-modal', 'true'); card.setAttribute('aria-label', title);
        const head = document.createElement('div'); head.className = 'mfg-modal-head';
        const h = document.createElement('h2'); h.textContent = title;
        const previous = document.activeElement;
        function close() { overlay.remove(); document.removeEventListener('keydown', keys); if (previous && previous.isConnected) previous.focus(); }
        function keys(e) {
            const overlays = document.querySelectorAll('.mfg-overlay');
            if (overlays[overlays.length - 1] !== overlay) return;
            if (e.key === 'Escape') close();
            if (e.key !== 'Tab') return;
            const items = Array.from(card.querySelectorAll('button, input, select, textarea, a[href]')).filter(x => !x.disabled && x.getClientRects().length);
            if (!items.length) return;
            if (e.shiftKey && document.activeElement === items[0]) { e.preventDefault(); items[items.length - 1].focus(); }
            else if (!e.shiftKey && document.activeElement === items[items.length - 1]) { e.preventDefault(); items[0].focus(); }
        }
        head.append(h, button(tr('close'), close)); card.append(head); overlay.append(card); document.body.append(overlay);
        overlay.addEventListener('click', e => { if (e.target === overlay) close(); }); document.addEventListener('keydown', keys);
        head.querySelector('button').focus(); return { overlay, card, close };
    }
    let metadata = { categories: [], tags: [] };
    async function loadMetadata() {
        const [categories, tags] = await Promise.all([list('/manufacturer-categories'), list('/manufacturer-tags')]);
        metadata = { categories, tags }; return metadata;
    }
    function tagChoices(container, selected, tags = metadata.tags) {
        container.replaceChildren(); container.className = 'mfg-tag-choices';
        tags.forEach(tag => {
            const label = document.createElement('label'); const input = document.createElement('input'); input.type = 'checkbox'; input.value = String(tag.id); input.checked = selected.map(String).includes(String(tag.id));
            label.append(input, document.createTextNode((tag.category_name ? tag.category_name + ': ' : '') + tag.name)); container.append(label);
        });
    }
    function selectedTags(container) { return Array.from(container.querySelectorAll('input:checked'), i => Number(i.value)); }
    function categoryOptions(select, blank) {
        select.replaceChildren(new Option(blank, ''));
        metadata.categories.forEach(c => select.add(new Option(c.name, c.id)));
    }
    async function openEditor(m, onSaved) {
        const view = modal(tr(m ? 'edit' : 'create'));
        const notice = document.createElement('div'); view.card.append(notice); notice.textContent = tr('loading');
        try { await loadMetadata(); } catch (error) { errorMessage(notice, error, () => { view.close(); openEditor(m, onSaved); }); return; }
        if (!view.overlay.isConnected) return;
        notice.textContent = '';
        const form = document.createElement('form'); form.className = 'mfg-form'; view.card.append(form);
        const fields = {};
        function field(key, value, type = 'text') {
            const label = document.createElement('label'); label.textContent = tr(key);
            const input = document.createElement(type === 'textarea' ? 'textarea' : 'input'); if (type !== 'textarea') input.type = type;
            input.value = value || ''; if (key === 'name') input.required = true; label.append(input); form.append(label); fields[key] = input;
        }
        field('name', m && m.name); field('address', m && m.address); field('notes', m && m.notes, 'textarea');
        const activeLabel = document.createElement('label'); const active = document.createElement('input'); active.type = 'checkbox'; active.checked = !m || isActive(m); activeLabel.append(active, document.createTextNode(tr('active'))); form.append(activeLabel);
        function rows(key, values, specs) {
            const group = document.createElement('fieldset'); const legend = document.createElement('legend'); legend.textContent = tr(key); group.append(legend);
            const container = document.createElement('div'); group.append(container);
            function addRow(value = {}) {
                const row = document.createElement('div'); row.className = 'mfg-contact-row';
                specs.forEach(([prop, type]) => { const input = document.createElement('input'); input.type = type; input.dataset.key = prop; input.value = value[prop] || ''; input.placeholder = tr(prop); input.setAttribute('aria-label', tr(prop)); row.append(input); });
                row.append(button(tr('remove'), () => row.remove())); container.append(row);
            }
            (values.length ? values : [{}]).forEach(addRow); group.append(button(tr('add'), () => addRow())); form.append(group);
            return () => Array.from(container.children, row => Object.fromEntries(Array.from(row.querySelectorAll('input'), i => [i.dataset.key, i.value.trim()]))).filter(value => specs.some(([prop]) => value[prop]));
        }
        const phones = (m && m.phones || []).slice(); if (m && m.phone && !phones.some(p => p.phone === m.phone)) phones.unshift({ phone: m.phone });
        const getPhones = rows('phones', phones, [['phone', 'tel']]);
        const getEmails = rows('emails', m && m.emails || [], [['email', 'email']]);
        const getSocials = rows('socials', m && m.socials || [], [['platform', 'text'], ['handle', 'text']]);
        const tagGroup = document.createElement('fieldset'); const legend = document.createElement('legend'); legend.textContent = tr('tags'); tagGroup.append(legend);
        const tags = document.createElement('div'); tagChoices(tags, (m && m.tags || []).map(tag => tag.id)); tagGroup.append(tags);
        tagGroup.append(button(tr('taxonomy'), () => openTaxonomy(async () => {
            const selected = selectedTags(tags); await loadMetadata(); if (view.overlay.isConnected) tagChoices(tags, selected);
        }))); form.append(tagGroup);
        const save = document.createElement('button'); save.type = 'submit'; save.className = 'mfg-button mfg-primary'; save.textContent = tr('save'); form.append(save, button(tr('cancel'), view.close));
        form.addEventListener('submit', async e => {
            e.preventDefault(); if (!fields.name.value.trim()) { notice.textContent = tr('nameRequired'); return; }
            const socials = getSocials();
            if (socials.some(s => !s.platform || !s.handle)) { notice.textContent = tr('socials') + ': ' + tr('platform') + ' / ' + tr('handle'); return; }
            const payload = { name: fields.name.value.trim(), address: fields.address.value.trim(), notes: fields.notes.value.trim(), is_active: active.checked, phones: getPhones(), emails: getEmails(), socials, tag_ids: selectedTags(tags) };
            payload.phone = payload.phones[0] && payload.phones[0].phone || '';
            save.disabled = true; notice.textContent = tr('saving');
            try {
                const saved = await request('/manufacturers' + (m ? '/' + encodeURIComponent(m.id) : ''), { method: m ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                view.close(); if (onSaved) onSaved(saved);
            } catch (error) { errorMessage(notice, error); } finally { save.disabled = false; }
        }); fields.name.focus();
    }
    async function openTaxonomy(onChanged) {
        const view = modal(tr('taxonomy')); const body = document.createElement('div'); body.className = 'mfg-form'; view.card.append(body);
        async function render() {
            body.textContent = tr('loading');
            try { await loadMetadata(); } catch (error) { errorMessage(body, error, render); return; }
            if (!view.overlay.isConnected) return;
            body.replaceChildren(); const hint = document.createElement('p'); hint.textContent = tr('suggestions'); body.append(hint);
            const notice = document.createElement('div'); body.append(notice);
            async function save(path, method, payload) {
                try { await request(path, { method, ...(method === 'DELETE' ? {} : { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }) }); await render(); if (onChanged) await onChanged(); }
                catch (error) { errorMessage(notice, error); }
            }
            function section(key, records, path) {
                const h = document.createElement('h3'); h.textContent = tr(key); body.append(h);
                function row(record) {
                    const form = document.createElement('form'); form.className = 'mfg-contact-row';
                    const input = document.createElement('input'); input.required = true; input.value = record && record.name || ''; input.placeholder = tr(record ? 'name' : key === 'categories' ? 'newCategory' : 'newTag'); input.setAttribute('aria-label', input.placeholder); form.append(input);
                    let select;
                    if (key === 'tags') {
                        select = document.createElement('select'); select.required = true; select.setAttribute('aria-label', tr('category'));
                        categoryOptions(select, tr('selectCategory'));
                        select.value = String(record && record.category_id || metadata.categories[0] && metadata.categories[0].id || '');
                        select.addEventListener('invalid', () => { notice.textContent = tr('categoryRequired'); });
                        form.append(select);
                    }
                    const submit = document.createElement('button'); submit.className = 'mfg-button'; submit.textContent = tr(record ? 'save' : 'add'); form.append(submit);
                    if (record) {
                        const remove = button(tr('deleteDefinition'), async () => {
                            if (!window.confirm(tr('confirmDelete') + ' "' + record.name + '"')) return;
                            remove.disabled = true; submit.disabled = true;
                            await save(path + '/' + encodeURIComponent(record.id), 'DELETE');
                            remove.disabled = false; submit.disabled = false;
                        });
                        remove.setAttribute('aria-label', tr('deleteDefinition') + ' ' + record.name); form.append(remove);
                    }
                    form.addEventListener('submit', async e => {
                        e.preventDefault(); if (!input.value.trim()) return;
                        const categoryId = select && Number(select.value);
                        if (select && (!Number.isInteger(categoryId) || !metadata.categories.some(c => Number(c.id) === categoryId))) {
                            notice.textContent = tr('categoryRequired'); select.focus(); return;
                        }
                        submit.disabled = true;
                        await save(path + (record ? '/' + encodeURIComponent(record.id) : ''), record ? 'PUT' : 'POST', { name: input.value.trim(), ...(select ? { category_id: categoryId } : {}) });
                        submit.disabled = false;
                    }); body.append(form);
                }
                records.forEach(row); row(null);
            }
            section('categories', metadata.categories, '/manufacturer-categories'); section('tags', metadata.tags, '/manufacturer-tags');
        }
        await render();
    }
    const api = { tr, esc, request, list, query, isActive, contacts, summary, exportExcel, errorMessage, modal, loadMetadata, tagChoices, selectedTags, categoryOptions, openEditor, openTaxonomy };
    window.ManufacturerUI = api;

    const root = document.getElementById('manufacturer-dashboard'); if (!root) return;
    let language = localStorage.getItem('appLang') === 'en' ? 'en' : 'fa';
    let records = []; let loaded = false; let revision = 0; let timer; let metadataReady = false;
    const filters = { q: '', active: 'all', tag_ids: [], category_id: '' };
    const $ = id => document.getElementById(id);
    function applyLanguage() {
        document.documentElement.lang = language; document.documentElement.dir = language === 'fa' ? 'rtl' : 'ltr';
        document.title = tr('title'); document.querySelectorAll('[data-mfg-text]').forEach(el => { el.textContent = tr(el.dataset.mfgText); });
        $('directory-search').placeholder = tr('search'); $('directory-lang').textContent = language === 'fa' ? 'EN' : 'فارسی';
        const active = $('directory-active'); active.replaceChildren(new Option(tr('all'), 'all'), new Option(tr('active'), 'true'), new Option(tr('inactive'), 'false')); active.value = filters.active;
        updateMetadataControls(); render();
    }
    function updateMetadataControls() {
        api.categoryOptions($('directory-category'), tr('anyCategory')); $('directory-category').value = filters.category_id;
        tagChoices($('directory-tags'), filters.tag_ids);
    }
    function theme() {
        const value = localStorage.getItem('theme') || 'light'; document.documentElement.dataset.theme = value;
        $('directory-theme').textContent = value === 'dark' ? 'Light / روشن' : 'Dark / تیره';
        document.documentElement.style.fontSize = ({ small: '12px', medium: '14px', large: '16px' })[localStorage.getItem('fontSize')] || '14px';
    }
    function render() {
        const listEl = $('directory-list'); listEl.replaceChildren(); $('directory-count').textContent = loaded ? records.length : '—';
        if (!loaded) return;
        if (!records.length) { const p = document.createElement('p'); p.textContent = tr('empty'); listEl.append(p); return; }
        records.forEach(m => {
            const card = document.createElement('article'); card.className = 'mfg-directory-card';
            card.innerHTML = `<div class="mfg-card-heading"><h2 dir="auto">${esc(m.name)}</h2><span class="mfg-chip ${isActive(m) ? '' : 'mfg-inactive'}">${tr(isActive(m) ? 'active' : 'inactive')}</span></div>${summary(m)}<p dir="auto">${esc(m.address)}</p><p class="mfg-notes" dir="auto">${esc(m.notes)}</p>`;
            const actions = document.createElement('div'); actions.className = 'mfg-actions';
            actions.append(button(tr('edit'), () => openEditor(m, reload)), button(tr('exportOne'), () => runExport('/manufacturers/' + encodeURIComponent(m.id) + '/export/excel'))); card.append(actions); listEl.append(card);
        });
    }
    async function runExport(path) { try { await exportExcel(path); } catch (error) { errorMessage($('directory-status'), error); } }
    async function reload() {
        const own = ++revision; $('directory-status').className = 'mfg-message'; $('directory-status').textContent = tr('loading');
        try {
            const data = await list('/manufacturers?' + query(filters)); if (own !== revision) return;
            records = data; loaded = true; render(); $('directory-status').textContent = '';
        } catch (error) { if (own === revision) errorMessage($('directory-status'), error, reload); }
    }
    async function refreshMetadata() {
        try { await loadMetadata(); metadataReady = true; updateMetadataControls(); $('directory-metadata-error').replaceChildren(); }
        catch (error) { metadataReady = false; errorMessage($('directory-metadata-error'), error, refreshMetadata); }
    }
    $('directory-search').addEventListener('input', e => { filters.q = e.target.value; clearTimeout(timer); timer = setTimeout(reload, 250); });
    $('directory-active').addEventListener('change', e => { filters.active = e.target.value; reload(); });
    $('directory-category').addEventListener('change', e => { filters.category_id = e.target.value; reload(); });
    $('directory-tags').addEventListener('change', () => { filters.tag_ids = selectedTags($('directory-tags')); reload(); });
    $('directory-new').addEventListener('click', () => openEditor(null, reload));
    $('directory-taxonomy').addEventListener('click', () => openTaxonomy(async () => { await refreshMetadata(); if (metadataReady) reload(); }));
    $('directory-export-all').addEventListener('click', () => runExport('/manufacturers/export/excel?active=all'));
    $('directory-export-filtered').addEventListener('click', () => runExport('/manufacturers/export/excel?' + query(filters)));
    $('directory-lang').addEventListener('click', () => { language = language === 'fa' ? 'en' : 'fa'; localStorage.setItem('appLang', language); applyLanguage(); });
    $('directory-theme').addEventListener('click', () => { localStorage.setItem('theme', document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'); theme(); });
    applyLanguage(); theme(); refreshMetadata(); reload();
})();
