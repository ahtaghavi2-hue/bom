let currentNodeId = null;
let currentData = { nodes: {}, root_ids: [] };
let tempStages = [];
let openedNodes = [];
let currentView = 'tree';
let currentMainView = 'tree';
let inlineEditContext = null;
let stageDetailsMap = {};
let partManufacturers = [];
let allManufacturers = [];
let expandedStages = {};
let _autoSaveTimer = null;
const nodeDrafts = new Map();
const pendingNodeSaves = new Map();
const queuedNodeSaves = new Set();
const persistedStageIds = new Map(); // Per-node temporary identity -> backend ID; never browser storage.
let saveQueue = Promise.resolve();
let saveRevision = 0;
let dataLoadRevision = 0;

// ───── Language / i18n ─────
const LANG = {
    fa: {
        name: 'فارسی',
        save: 'ذخیره',
        saving: 'در حال ذخیره...',
        saved: 'ذخیره شد',
        error: 'خطا',
        cancel: 'انصراف',
        confirm: 'تأیید',
        ok: 'باشه',
        yes: 'بله',
        no: 'خیر',
        delete: 'حذف',
        add: 'افزودن',
        edit: 'ویرایش',
        close: 'بستن',
        search: 'جستجو',
        product: 'محصول',
        assembly: 'زیرمجموعه',
        part: 'قطعه',
        newProduct: 'محصول جدید',
        newAssembly: 'زیرمجموعه جدید',
        newPart: 'قطعه جدید',
        name: 'نام',
        partCode: 'کد فنی',
        specs: 'مشخصات فنی',
        notes: 'یادداشت',
        quantity: 'تعداد',
        requiredQuantity: 'تعداد لازم برای ساخت یک والد',
        coefficientHelp: 'تعداد لازم برای ساخت یک واحد از والد مستقیم',
        targetHelp: 'تعداد هدف محصول؛ موجودی آماده از این تعداد کسر می‌شود.',
        allItems: 'کل اقلام',
        stock: 'موجودی',
        supplier: 'تأمین‌کننده',
        supplierEmail: 'ایمیل تأمین‌کننده',
        type: 'نوع',
        buy: 'خریدنی',
        make: 'ساختنی',
        status: 'وضعیت',
        notStarted: 'شروع نشده',
        inProgress: 'در حال اجرا',
        completed: 'تکمیل شده',
        shortage: 'کسری موجودی',
        partialStock: 'موجودی ناقص',
        sufficient: 'موجودی کافی',
        noStages: 'هنوز مرحله‌ای تعریف نشده',
        addStage: 'افزودن مرحله',
        stageName: 'نام مرحله',
        stageDetails: 'جزئیات تولید',
        addDetail: 'افزودن جزئیات',
        manufacturers: 'سازندگان قطعه',
        addManufacturer: 'افزودن سازنده',
        noManufacturer: 'هیچ سازنده‌ای ثبت نشده',
        createManufacturer: 'ایجاد سازنده جدید',
        selectManufacturer: 'انتخاب سازنده',
        allAdded: 'همه سازنده‌ها قبلاً اضافه شده‌اند',
        confirmDelete: 'آیا از حذف مطمئن هستید؟',
        saveSuccess: 'با موفقیت ذخیره شد',
        saveError: 'خطا در ذخیره',
        loading: 'در حال بارگذاری...',
        noSelection: 'یک گره از درخت را انتخاب کنید',
        noDocuments: 'هیچ مدرک فنی بارگذاری نشده',
        noSchedules: 'برنامه‌ای ثبت نشده',
        noImages: 'بدون عکس',
        material: 'مواد',
        labor: 'دستمزد',
        overhead: 'سربار',
        hours: 'ساعت',
        total: 'مجموع',
        cost: 'هزینه',
        email: 'ایمیل',
        phone: 'تلفن',
        address: 'آدرس',
        social: 'شبکه اجتماعی',
        platform: 'پلتفرم',
        handle: 'آیدی',
        productStructure: 'ساختار محصول',
        treeView: 'درختی',
        kanbanView: 'کانبان',
        excelExport: 'Excel',
        schematicExport: 'شماتیک',
        settings: 'تنظیمات',
        logout: 'خروج',
        notifications: 'اعلان‌ها',
        noNotification: 'هیچ اعلانی وجود ندارد',
        dashboard: 'داشبورد',
        schedule: 'برنامه تولید',
        addSchedule: 'برنامه جدید',
        techDocs: 'مدارک فنی',
        images: 'تصاویر',
        inventory: 'انبار',
        manufacturing: 'ساخت',
        general: 'عمومی',
        detailText: 'متن جزئیات',
        orderCount: 'تعداد هدف محصول',
        totalRequired: 'تعداد مورد نیاز کل',
        progress: 'پیشرفت مراحل ساخت',
        completedCount: 'تکمیل شده',
        remainingCount: 'باقی‌مانده',
        newSchedule: 'برنامه تولید جدید',
        scheduleQuantity: 'تعداد سفارش',
        startDate: 'تاریخ شروع',
        endDate: 'تاریخ پایان',
        productForExport: 'انتخاب محصول برای خروجی',
        noProduct: 'هیچ محصولی تعریف نشده',
        invalidNumber: 'عدد نامعتبر',
        stageRequired: 'لطفاً نام مرحله را وارد کنید',
        nameRequired: 'نام الزامی است',
        selectNode: 'ابتدا یک گره را انتخاب کنید',
        partNoChildren: 'قطعه نمی‌تواند زیرمجموعه داشته باشد',
        langToggle: 'English',
        langDir: 'rtl',
        imageLabel: 'برچسب عکس',
        imageLabelDefault: 'تصویر',
        notStartedShort: 'شروع نشده',
        inProgressShort: 'در حال ساخت',
        completedShort: 'ساخته شده',
        shortage2: 'کسری',
        available: 'موجود',
        required: 'نیاز',
        order: 'سفارش',
        stagesCount: 'مرحله',
        selectOption: '-- انتخاب کنید --',
        code: 'کد',
        download: 'دانلود',
        sendEmail: 'ارسال ایمیل',
        planned: 'برنامه‌ریزی شده',
        cancelled: 'لغو شده',
        priority: 'اولویت',
        start: 'شروع',
        end: 'پایان',
        materialCost: 'هزینه مواد برآوردی',
        laborCost: 'دستمزد برآوردی',
        overheadCost: 'سربار برآوردی',
        estimatedHours: 'ساعت برآوردی',
        hoverStock: 'موجودی',
        hoverTotalReq: 'نیاز کل',
        hoverSufficient: 'موجودی کافی',
        hoverPartial: 'موجودی ناقص',
        hoverShortage: 'کسری انبار',
        hoverType: 'نوع',
        mfrInfo: 'اطلاعاتی ثبت نشده',
        mfrEmail: 'ایمیل',
        mfrPhone: 'تلفن',
        mfrAddress: 'آدرس',
        mfrNotes: 'یادداشت',
        mfrSocial: 'شبکه اجتماعی',
    },
    en: {
        name: 'English',
        save: 'Save',
        saving: 'Saving...',
        saved: 'Saved',
        error: 'Error',
        cancel: 'Cancel',
        confirm: 'Confirm',
        ok: 'OK',
        yes: 'Yes',
        no: 'No',
        delete: 'Delete',
        add: 'Add',
        edit: 'Edit',
        close: 'Close',
        search: 'Search',
        product: 'Product',
        assembly: 'Assembly',
        part: 'Part',
        newProduct: 'New Product',
        newAssembly: 'New Assembly',
        newPart: 'New Part',
        name: 'Name',
        partCode: 'Part Code',
        specs: 'Specifications',
        notes: 'Notes',
        quantity: 'Quantity',
        requiredQuantity: 'Units needed per immediate parent',
        coefficientHelp: 'Units needed to build ONE unit of the immediate parent',
        targetHelp: 'Product target count; ready stock is deducted from this target.',
        allItems: 'All Items',
        stock: 'Stock',
        supplier: 'Supplier',
        supplierEmail: 'Supplier Email',
        type: 'Type',
        buy: 'Buy',
        make: 'Make',
        status: 'Status',
        notStarted: 'Not Started',
        inProgress: 'In Progress',
        completed: 'Completed',
        shortage: 'Stock Shortage',
        partialStock: 'Partial Stock',
        sufficient: 'Sufficient Stock',
        noStages: 'No stages defined yet',
        addStage: 'Add Stage',
        stageName: 'Stage Name',
        stageDetails: 'Production Details',
        addDetail: 'Add Detail',
        manufacturers: 'Part Manufacturers',
        addManufacturer: 'Add Manufacturer',
        noManufacturer: 'No manufacturer registered',
        createManufacturer: 'Create New Manufacturer',
        selectManufacturer: 'Select Manufacturer',
        allAdded: 'All manufacturers already added',
        confirmDelete: 'Are you sure you want to delete?',
        saveSuccess: 'Saved successfully',
        saveError: 'Save error',
        loading: 'Loading...',
        noSelection: 'Select a node from the tree',
        noDocuments: 'No technical documents uploaded',
        noSchedules: 'No schedules registered',
        noImages: 'No images',
        material: 'Material',
        labor: 'Labor',
        overhead: 'Overhead',
        hours: 'Hours',
        total: 'Total',
        cost: 'Cost',
        email: 'Email',
        phone: 'Phone',
        address: 'Address',
        social: 'Social Media',
        platform: 'Platform',
        handle: 'ID',
        productStructure: 'Product Structure',
        treeView: 'Tree',
        kanbanView: 'Kanban',
        excelExport: 'Excel',
        schematicExport: 'Schematic',
        settings: 'Settings',
        logout: 'Logout',
        notifications: 'Notifications',
        noNotification: 'No notifications',
        dashboard: 'Dashboard',
        schedule: 'Schedule',
        addSchedule: 'New Schedule',
        techDocs: 'Tech Docs',
        images: 'Images',
        inventory: 'Inventory',
        manufacturing: 'Manufacturing',
        general: 'General',
        detailText: 'Detail Text',
        orderCount: 'Product Target Count',
        totalRequired: 'Total Required',
        progress: 'Production Progress',
        completedCount: 'Completed',
        remainingCount: 'Remaining',
        newSchedule: 'New Production Schedule',
        scheduleQuantity: 'Order Quantity',
        startDate: 'Start Date',
        endDate: 'End Date',
        productForExport: 'Select Product',
        noProduct: 'No products defined',
        invalidNumber: 'Invalid number',
        stageRequired: 'Please enter a stage name',
        nameRequired: 'Name is required',
        selectNode: 'Please select a node first',
        partNoChildren: 'Part cannot have children',
        langToggle: 'فارسی',
        langDir: 'ltr',
        imageLabel: 'Image Label',
        imageLabelDefault: 'Image',
        notStartedShort: 'Not Started',
        inProgressShort: 'In Progress',
        completedShort: 'Completed',
        shortage2: 'Shortage',
        available: 'Available',
        required: 'Required',
        order: 'Order',
        stagesCount: 'Stages',
        selectOption: '-- Select --',
        code: 'Code',
        download: 'Download',
        sendEmail: 'Send Email',
        planned: 'Planned',
        cancelled: 'Cancelled',
        priority: 'Priority',
        start: 'Start',
        end: 'End',
        materialCost: 'Estimated Material Cost',
        laborCost: 'Estimated Labor Cost',
        overheadCost: 'Estimated Overhead',
        estimatedHours: 'Estimated Hours',
        hoverStock: 'Stock',
        hoverTotalReq: 'Total Required',
        hoverSufficient: 'Stock Sufficient',
        hoverPartial: 'Partial Stock',
        hoverShortage: 'Stock Shortage',
        hoverType: 'Type',
        mfrInfo: 'No info registered',
        mfrEmail: 'Email',
        mfrPhone: 'Phone',
        mfrAddress: 'Address',
        mfrNotes: 'Notes',
        mfrSocial: 'Social',
    }
};

let currentLang = localStorage.getItem('appLang') === 'en' ? 'en' : 'fa';

function t(key) {
    return LANG[currentLang][key] || key;
}

function toggleLang() {
    currentLang = currentLang === 'fa' ? 'en' : 'fa';
    localStorage.setItem('appLang', currentLang);
    document.documentElement.setAttribute('dir', t('langDir'));
    applyLang();
}

function applyLang() {
    document.documentElement.setAttribute('dir', t('langDir'));
    document.documentElement.setAttribute('lang', currentLang);
    $('#manufacturers-link').text(currentLang === 'fa' ? 'دفتر سازندگان' : 'Manufacturer directory');
    $('#part-manufacturers-label').text(currentLang === 'fa' ? 'سازندگان مستقل قطعه (جدا از مراحل)' : 'Standalone part manufacturers (separate from stages)');
    $('#part-manufacturers-add').text(t('addManufacturer'));
    $('#lang-toggle').text(t('langToggle'));
    $('#app-title').text(currentLang === 'fa' ? '🏭 سیستم مدیریت ساخت محصول' : '🏭 BOM & Production Manager');
    $('#settings-link').text('⚙ ' + t('settings'));
    $('#logout-link').text(t('logout'));
    $('#tree-panel-title').text(t('productStructure'));
    $('#btn-view-tree').text(' ' + t('treeView'));
    $('#btn-view-kanban').text(' ' + t('kanbanView'));
    $('#btn-excel').text('📊 ' + t('excelExport'));
    $('#btn-schematic').text('📐 ' + t('schematicExport'));
    $('#no-selection p').text('👈 ' + t('noSelection'));
    $('#tab-btn-general').text(t('general'));
    $('#tab-btn-images').text('️ ' + t('images'));
    $('#tab-btn-inventory').text('📦 ' + t('inventory'));
    $('#tab-btn-mfg').text('⚙️ ' + t('manufacturing'));
    $('#tab-btn-schedule').text('📅 ' + t('schedule'));
    $('#tab-btn-docs').text('📁 ' + t('techDocs'));
    $('#field-name-label').text(t('name'));
    $('#field-partCode-label').text(t('partCode'));
    $('#field-specs-label').text(t('specs'));
    $('#field-notes-label').text(t('notes'));
    $('#field-required_quantity-label').text(t('requiredQuantity'));
    $('#field-quantity-label').text(t('stock'));
    $('#field-order_count-label').text(t('orderCount'));
    $('#field-total_required-label').text(t('totalRequired'));
    $('#field-supplier-label').text(t('supplier'));
    $('#field-supplier-email-label').text(t('supplierEmail'));
    $('#field-partType-label').text(t('partType'));
    $('#btn-add-assembly').text('📦 ' + t('newAssembly'));
    $('#btn-add-part').text('⚙️ ' + t('newPart'));
    $('#btn-delete').html('️ ' + t('delete'));
    $('#add-image-label').text(t('images'));
    $('#add-doc-label').text(t('techDocs'));
    $('#part-email-label').text(t('supplierEmail'));
    $('#gallery-label').text(t('images') + ':');
    $('#send-email-text').text(t('sendEmail'));
    $('#send-email-btn').prop('title', t('sendEmail'));
    $('#email-desc').text(currentLang === 'fa' ? 'برای اطلاع از کمبود موجودی یا وضعیت ساخت به این آدرس ایمیل ارسال می‌شود' : 'Emails are sent to this address for shortage alerts and production status updates.');
    $('#status-label').text(t('status'));
    $('#status-txt-notstarted').text(t('shortage'));
    $('#status-txt-inprogress').text(t('partialStock'));
    $('#status-txt-completed').text(t('sufficient'));
    $('#cost-label').text(t('cost') + ':');
    $('#stages-label').text(t('manufacturing') + ':');
    $('#new-stage-name').attr('placeholder', t('stageName'));
    $('#add-stage-btn-text').text(t('add'));
    $('#schedule-label').text(t('schedule') + ':');
    $('#add-schedule-btn-text').text(t('addSchedule'));
    $('#docs-label').text(t('techDocs') + ':');
    $('#progress-label-text').text(t('progress'));
    $('#stat-total-label').text(t('allItems'));
    if (currentData.nodes[currentNodeId]) {
        updateInventoryHelp(currentData.nodes[currentNodeId]);
        refreshDemandViews();
    }
    $('#stat-done-label').text(t('completedCount'));
    $('#stat-missing-label').text(t('shortage'));
    // modal buttons
    $('.btn-ok').text(t('ok'));
    $('.btn-yes').text(t('yes'));
    $('.btn-no').text(t('no'));
    $('.btn-cancel').text(t('cancel'));
    $('.btn-confirm').text(t('confirm'));
    $('.btn-save-modal').text(t('save'));
    updateProgressBar();
}

$(document).ready(function() {
    const savedLang = localStorage.getItem('appLang') === 'en' ? 'en' : 'fa';
    currentLang = savedLang;
    document.documentElement.setAttribute('dir', t('langDir'));
    applyLang();

    // بارگذاری تم ذخیره‌شده
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
    // restore font size
    const savedFontSize = localStorage.getItem('fontSize') || 'medium';
    const sizeMap = { small: '12px', medium: '14px', large: '16px' };
    document.documentElement.style.fontSize = sizeMap[savedFontSize] || '14px';

    // Shared pages restore preferences but must not initialize BOM controls or requests.
    if (!document.getElementById('tree-container')) return;

    const savedOpened = localStorage.getItem('openedNodes');
    try {
        const parsed = savedOpened ? JSON.parse(savedOpened) : [];
        openedNodes = Array.isArray(parsed) ? parsed : [];
    } catch (error) { openedNodes = []; }

    const actionsDiv = document.querySelector('.form-actions');
    const btnAddAssembly = document.createElement('button');
    btnAddAssembly.textContent = '📦 ' + (window.t ? t('newAssembly') : 'افزودن زیرمجموعه');
    btnAddAssembly.id = 'btn-add-assembly';
    btnAddAssembly.className = 'btn-add';
    btnAddAssembly.style.background = '#3498db';
    btnAddAssembly.onclick = () => addChildOf('assembly');

    const btnAddPart = document.createElement('button');
    btnAddPart.textContent = '⚙️ ' + (window.t ? t('newPart') : 'افزودن قطعه');
    btnAddPart.id = 'btn-add-part';
    btnAddPart.className = 'btn-add';
    btnAddPart.style.background = '#9b59b6';
    btnAddPart.onclick = () => addChildOf('part');

    actionsDiv.insertBefore(btnAddPart, actionsDiv.firstChild);
    actionsDiv.insertBefore(btnAddAssembly, actionsDiv.firstChild);

    loadData();
    loadNotifications();
});

function validBomData(data) {
    return !!data && typeof data === 'object' && !!data.nodes && typeof data.nodes === 'object'
        && !Array.isArray(data.nodes) && Array.isArray(data.root_ids)
        && Object.values(data.nodes).every(node => node && typeof node === 'object'
            && ['product', 'assembly', 'part'].includes(node.type))
        && data.root_ids.every(id => Object.prototype.hasOwnProperty.call(data.nodes, id));
}

function loadData() {
    const revision = ++dataLoadRevision;
    const status = document.getElementById('data-load-status');
    if (status) { status.className = 'mfg-message'; status.textContent = t('loading'); }
    return fetch('/api/data')
        .then(res => {
            if (!res.ok) throw new Error('HTTP ' + res.status);
            return res.json();
        })
        .then(data => {
            if (revision !== dataLoadRevision) return;
            if (!validBomData(data)) throw new Error(currentLang === 'fa' ? 'ساختار پاسخ نامعتبر است' : 'Invalid product-data response');
            nodeDrafts.forEach((draft, id) => {
                if (data.nodes[id]) Object.assign(data.nodes[id], JSON.parse(JSON.stringify(draft.payload)));
            });
            currentData = data;
            recalculateDemand();
            updateStageSuggestions();
            updateDashboard();
            if (currentMainView === 'tree') renderTree();
            else if (currentMainView === 'kanban') {
                renderKanban();
                if (currentData.nodes[currentNodeId]) showEditForm(currentData.nodes[currentNodeId]);
            }
            if (status) status.replaceChildren();
            return true;
        }).catch(error => {
            if (revision !== dataLoadRevision) return false;
            if (status) {
                status.className = 'mfg-message mfg-error'; status.replaceChildren();
                const message = document.createElement('p');
                message.textContent = (currentLang === 'fa'
                    ? 'بارگذاری اطلاعات محصولات ناموفق بود. اتصال، ورود به حساب و مسیر /api/data را بررسی کنید. اطلاعات قبلی حفظ شده است؛ فهرست خالی به معنی نبود محصول نیست. '
                    : 'Product data could not be loaded. Check your connection, sign-in and /api/data availability. Existing data is retained; an empty view does not mean there are no products. ') + error.message;
                const retry = document.createElement('button'); retry.type = 'button'; retry.className = 'mfg-button';
                retry.textContent = currentLang === 'fa' ? 'تلاش مجدد' : 'Retry'; retry.onclick = loadData;
                status.append(message, retry);
            }
            return false;
        });
}

function loadNotifications() {
    fetch('/api/notifications')
        .then(res => res.json())
        .then(notifs => {
            $('#shortage-count').text(notifs.shortage.length);
            $('#progress-count').text(notifs.in_progress.length);
            $('#order-count-notif').text(notifs.orders_pending.length);

            const totalNotifs = notifs.shortage.length + notifs.in_progress.length + notifs.orders_pending.length;
            if (totalNotifs > 0) {
                $('#notif-badge').text(totalNotifs).show();
            } else {
                $('#notif-badge').hide();
            }

            const shortageList = $('#shortage-list');
            shortageList.empty();
            if (notifs.shortage.length === 0) {
                shortageList.html('<div style="color:var(--text-muted); font-size:12px; padding:8px;">✅ ' + t('noSelection') + '</div>');
            } else {
                notifs.shortage.forEach(item => {
                    shortageList.append(`
                        <div class="notif-item" onclick="goToNode('${item.id}')">
                            <strong>${item.name}</strong><br>
                            <span style="color:var(--feedback-danger-text);">${t('shortage2')}: ${item.shortage}</span>
                            <span style="color:var(--text-muted);"> (${t('available')}: ${item.available} / ${t('required')}: ${item.required})</span>
                        </div>
                    `);
                });
            }

            const progressList = $('#progress-list');
            progressList.empty();
            if (notifs.in_progress.length === 0) {
                progressList.html('<div style="color:var(--text-muted); font-size:12px; padding:8px;">' + t('noNotification') + '</div>');
            } else {
                notifs.in_progress.forEach(item => {
                    progressList.append(`
                        <div class="notif-item" style="border-right-color:#FF9800;" onclick="goToNode('${item.id}')">
                            <strong>${item.name}</strong><br>
                            <span style="color:var(--text-secondary);">${item.stages} ${t('stagesCount')}</span>
                        </div>
                    `);
                });
            }

            const orderList = $('#order-list');
            orderList.empty();
            if (notifs.orders_pending.length === 0) {
                orderList.html('<div style="color:var(--text-muted); font-size:12px; padding:8px;">' + t('noSchedules') + '</div>');
            } else {
                notifs.orders_pending.forEach(item => {
                    orderList.append(`
                        <div class="notif-item" style="border-right-color:#3498db;" onclick="goToNode('${item.id}')">
                            <strong>${item.name}</strong><br>
                            <span style="color:var(--text-secondary);">${item.count} ${t('order')}</span>
                        </div>
                    `);
                });
            }
        });
}

function toggleNotifications() {
    const panel = $('#notification-panel');
    if (panel.is(':visible')) {
        panel.slideUp(200);
    } else {
        loadNotifications();
        panel.slideDown(200);
    }
}

function goToNode(nodeId) {
    toggleNotifications();
    if (currentData.nodes[nodeId]) {
        currentNodeId = nodeId;
        // باز کردن والدین
        let node = currentData.nodes[nodeId];
        while (node && node.parent) {
            if (!openedNodes.includes(node.parent)) {
                openedNodes.push(node.parent);
            }
            node = currentData.nodes[node.parent];
        }
        localStorage.setItem('openedNodes', JSON.stringify(openedNodes));
        renderTree();
        setTimeout(() => {
            $('#tree-container').jstree('select_node', nodeId);
        }, 300);
    }
}

function nonNegativeInt(value, fallback = 0) {
    const number = Number(value);
    return value === '' || value == null || !Number.isFinite(number)
        ? fallback : Math.max(0, Math.floor(number));
}

// Demand is passed only from the immediate parent's shortage, never its gross demand.
function recalculateDemand() {
    const visited = new Set();
    Object.values(currentData.nodes).forEach(node => {
        node.required_total = 0;
        node.shortage = 0;
        node.stock_used = 0;
    });
    function visit(nodeId, gross) {
        const node = currentData.nodes[nodeId];
        if (!node || visited.has(nodeId)) return;
        visited.add(nodeId);
        node.required_total = gross;
        const stock = nonNegativeInt(node.quantity);
        node.stock_used = Math.min(stock, gross);
        node.shortage = Math.max(gross - stock, 0);
        (node.children || []).forEach(childId => {
            const child = currentData.nodes[childId];
            if (child) visit(childId, node.shortage * nonNegativeInt(child.required_quantity, 1));
        });
    }
    currentData.root_ids.forEach(id => {
        const root = currentData.nodes[id];
        if (root) visit(id, nonNegativeInt(root.order_count));
    });
}

function inventoryStatus(node) {
    return node.shortage === 0 ? 'completed'
        : (nonNegativeInt(node.quantity) > 0 ? 'in_progress' : 'not_started');
}

function refreshDemandViews() {
    recalculateDemand();
    updateDashboard();
    calculateShortage();
    if (currentMainView === 'kanban') renderKanban();
    else {
        const tree = $('#tree-container').jstree(true);
        if (tree) Object.keys(currentData.nodes).forEach(id => {
            const built = buildTreeNode(id);
            if (tree.get_node(id)) {
                tree.set_text(id, built.text);
                const anchor = document.getElementById(id + '_anchor');
                if (anchor) anchor.style.color = inventoryStatus(currentData.nodes[id]) === 'completed'
                    ? 'var(--status-success-text)' : (inventoryStatus(currentData.nodes[id]) === 'in_progress' ? 'var(--status-warning-text)' : 'var(--status-danger-text)');
            }
        });
    }
}

function getBreadcrumbs(nodeId) {
    const breadcrumbs = [];
    let node = currentData.nodes[nodeId];
    while (node) {
        breadcrumbs.unshift({ id: node.id, name: node.name });
        if (node.parent) node = currentData.nodes[node.parent];
        else break;
    }
    return breadcrumbs;
}

function updateBreadcrumbs(nodeId) {
    const breadcrumbs = getBreadcrumbs(nodeId);
    const container = $('#breadcrumbs');
    if (breadcrumbs.length <= 1) {
        container.hide();
        return;
    }
    container.empty().show();
    breadcrumbs.forEach((item, idx) => {
        if (idx > 0) container.append('<span class="breadcrumb-separator">/</span>');
        const isCurrent = idx === breadcrumbs.length - 1;
        container.append(`<span class="breadcrumb-item ${isCurrent ? 'current' : ''}" onclick="${isCurrent ? '' : `goToNode('${item.id}')`}">${item.name}</span>`);
    });
}

function updateDashboard() {
    let total = 0, done = 0, missing = 0;
    Object.values(currentData.nodes).forEach(node => {
        total++;
        if (node.shortage === 0) done++;
        if (node.shortage > 0) missing++;
    });
    $('#stat-total').text(total);
    $('#stat-done').text(done);
    $('#stat-missing').text(missing);
    $('#dashboard-summary').show();
}

function updateStageSuggestions() {
    const stages = new Set();
    Object.values(currentData.nodes).forEach(node => {
        if (node.stages && Array.isArray(node.stages)) {
            node.stages.forEach(s => { if (s.name) stages.add(s.name); });
        }
    });
    const datalist = document.getElementById('stage-suggestions');
    datalist.innerHTML = '';
    stages.forEach(stage => {
        const option = document.createElement('option');
        option.value = stage;
        datalist.appendChild(option);
    });
}

function renderTree() {
    const treeData = currentData.root_ids.map(id => buildTreeNode(id));
    $('#tree-container').jstree('destroy').empty();

    $('#tree-container').jstree({
        'core': {
            'data': treeData,
            'themes': { 'dots': true, 'icons': true },
            'check_callback': function(operation, node, parent, position, more) {
                if (operation === 'move_node') {
                    function isDescendant(parentId, childId) {
                        var p = currentData.nodes[parentId];
                        if (!p) return false;
                        for (var i = 0; i < p.children.length; i++) {
                            if (p.children[i] === childId) return true;
                            if (isDescendant(p.children[i], childId)) return true;
                        }
                        return false;
                    }
                    if (isDescendant(node.id, parent.id)) return false;
                    var parentNode = currentData.nodes[parent.id];
                    if (parentNode && parentNode.type === 'part') return false;
                    return true;
                }
                return true;
            }
        },
        'plugins': ['search', 'dnd']
    }).on('select_node.jstree', function(e, data) {
        currentNodeId = data.node.id;
        showEditForm(currentData.nodes[currentNodeId]);
    }).on('after_open.jstree', function(e, data) {
        if (!openedNodes.includes(data.node.id)) {
            openedNodes.push(data.node.id);
            localStorage.setItem('openedNodes', JSON.stringify(openedNodes));
        }
    }).on('after_close.jstree', function(e, data) {
        const idx = openedNodes.indexOf(data.node.id);
        if (idx > -1) {
            openedNodes.splice(idx, 1);
            localStorage.setItem('openedNodes', JSON.stringify(openedNodes));
        }
    }).on('loaded.jstree', function() {
        openedNodes.forEach(nodeId => $('#tree-container').jstree('open_node', nodeId));
        if (currentNodeId && currentData.nodes[currentNodeId]) {
            $('#tree-container').jstree('select_node', currentNodeId);
        }
    }).on('move_node.jstree', function(e, data) {
        var movedId = data.node.id;
        var newParentId = data.parent;
        fetch(`/api/node/${movedId}/move`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ new_parent: newParentId })
        }).then(() => loadData());
    }).on('dblclick.jstree', function(e) {
        // دابل‌کلیک برای ویرایش سریع نام
        var node = $('#tree-container').jstree(true).get_node(e.target);
        if (node && node.id) {
            openInlineEdit(node.id, 'name', currentData.nodes[node.id].name);
        }
    });

    // Hover Cards
    setTimeout(() => {
        $('#tree-container').find('.jstree-anchor').on('mouseenter', function(e) {
            const nodeId = $(this).closest('.jstree-node').attr('id');
            if (nodeId) showHoverCard(nodeId, e);
        }).on('mouseleave', function() {
            hideHoverCard();
        }).on('mousemove', function(e) {
            moveHoverCard(e);
        });
    }, 500);
}

function showHoverCard(nodeId, e) {
    const node = currentData.nodes[nodeId];
    if (!node) return;

    let imgHtml = '<span style="color:var(--text-muted);">' + t('noImages') + '</span>';
    if (node.images && node.images.length > 0) {
        const url = node.images[0].url.startsWith('/') ? node.images[0].url : '/' + node.images[0].url;
        imgHtml = `<img src="${url}">`;
    }

    $('#hover-card-img').html(imgHtml);
    $('#hover-card-name').text(node.name);
    $('#hover-card-code').text(t('hoverType') + ': ' + t('code') + ': ' + (node.partCode || '-'));

    let stockText = '';
    let statusText = '';
    let statusColor = '';

    stockText = t('hoverStock') + ': ' + nonNegativeInt(node.quantity)
        + ' / ' + t('hoverTotalReq') + ': ' + node.required_total;
    const status = inventoryStatus(node);
    statusText = t('shortage2') + ': ' + node.shortage + ' — '
        + t(status === 'completed' ? 'hoverSufficient' : (status === 'in_progress' ? 'hoverPartial' : 'hoverShortage'));
    statusColor = status === 'completed' ? 'var(--status-success-text)' : (status === 'in_progress' ? 'var(--status-warning-text)' : 'var(--status-danger-text)');

    $('#hover-card-stock').text(stockText);
    $('#hover-card-status').text(statusText).css('color', statusColor);

    $('#hover-card').show();
    moveHoverCard(e);
}

function moveHoverCard(e) {
    const card = $('#hover-card');
    let x = e.pageX + 15;
    let y = e.pageY + 15;
    if (x + 280 > window.innerWidth) x = e.pageX - 295;
    if (y + 200 > window.innerHeight) y = e.pageY - 215;
    card.css({ left: x, top: y });
}

function hideHoverCard() {
    $('#hover-card').hide();
}

function searchTree(val) {
    $('#tree-container').jstree(true).search(val);
}

function buildTreeNode(nodeId) {
    const node = currentData.nodes[nodeId];
    if (!node) return null;
    let text = node.name;
    let color = 'var(--text-primary)';

    if (node.type === 'product') {
        text = '🏭 ' + text;
        if (node.order_count > 0) text += ` (${node.order_count} ${t('order')})`;
    } else if (node.type === 'assembly') {
        text = '📦 ' + text;
    } else if (node.type === 'part') {
        if (node.partType === 'buy') text = '🛒 ' + text;
        else if (node.partType === 'make') text = '🔧 ' + text;
        else text = '⚙️ ' + text;
    }

    const status = inventoryStatus(node);
    color = status === 'completed' ? 'var(--status-success-text)' : (status === 'in_progress' ? 'var(--status-warning-text)' : 'var(--status-danger-text)');

    return {
        id: nodeId, text: text, icon: false,
        a_attr: { style: `color: ${color}; font-weight: bold;` },
        children: node.children.map(cid => buildTreeNode(cid)).filter(c => c)
    };
}

function switchMainView(view) {
    currentMainView = view;
    $('#btn-view-tree').toggleClass('active', view === 'tree');
    $('#btn-view-kanban').toggleClass('active', view === 'kanban');
    if (view === 'tree') {
        $('#tree-container').show();
        $('#kanban-container').hide();
        renderTree();
    } else {
        $('#tree-container').hide();
        $('#kanban-container').show();
        renderKanban();
    }
}

function renderKanban() {
    const container = $('#kanban-container');
    container.empty();

    const columns = {
        'not_started': { title: '🔴 ' + t('notStartedShort') + ' / ' + t('shortage2'), cards: [] },
        'in_progress': { title: '🟡 ' + t('inProgressShort') + ' / ' + t('inProgress'), cards: [] },
        'completed': { title: '🟢 ' + t('completedShort') + ' / ' + t('sufficient'), cards: [] }
    };

    Object.values(currentData.nodes).forEach(node => {
        const status = inventoryStatus(node);
        columns[status].cards.push({
            id: node.id, name: node.name, type: node.type,
            code: node.partCode || '-',
            required: node.required_total, available: nonNegativeInt(node.quantity),
            shortage: node.shortage,
            stages: node.stages ? node.stages.length : 0
        });
    });

    const board = $('<div class="kanban-board"></div>');

    Object.entries(columns).forEach(([status, col]) => {
        const column = $(`
            <div class="kanban-column">
                <div class="kanban-column-header">
                    <span>${col.title}</span>
                    <span class="count">${col.cards.length}</span>
                </div>
                <div class="kanban-cards"></div>
            </div>
        `);

        col.cards.forEach(card => {
            const cardEl = $(`
                <div class="kanban-card status-${status.replace(/_/g, '-')}" onclick="goToNode('${card.id}')">
                    <div class="kanban-card-name">${card.name}</div>
                    <div class="kanban-card-info">${t('code')}: ${card.code}</div>
                    <div class="kanban-card-info">${t(card.type)} — ${t('hoverStock')}: ${card.available}</div>
                    <div class="kanban-card-info">${t('totalRequired')}: ${card.required} / ${t('shortage2')}: ${card.shortage}</div>
                    <div class="kanban-card-info">${card.stages} ${t('stagesCount')}</div>
                </div>
            `);
            column.find('.kanban-cards').append(cardEl);
        });

        board.append(column);
    });

    container.append(board);
}

function switchTab(tabId) {
    $('.tab-btn').removeClass('active');
    $('.tab-content').removeClass('active');
    $(`button[onclick="switchTab('${tabId}')"]`).addClass('active');
    $(`#${tabId}`).addClass('active');
}

// ───── Auto-save ─────

function normalizeStageIds(nodeId, stages) {
    const ids = persistedStageIds.get(nodeId);
    (stages || []).forEach(stage => {
        if (!stage.id && stage._tmpId && ids && ids.has(stage._tmpId)) stage.id = ids.get(stage._tmpId);
    });
}

function reconcileSavedStageIds(snapshot, savedNode) {
    const sent = snapshot.payload.stages;
    if (!sent || !savedNode || !Array.isArray(savedNode.stages)) return;
    // Only the immutable SENT order is positional. Live/queued lists may have been
    // edited, reordered or had stages removed while the request was in flight.
    const returned = savedNode.stages;
    const known = new Set(sent.filter(stage => stage.id).map(stage => String(stage.id)));
    const created = returned.filter(stage => !known.has(String(stage.id)));
    const newStages = sent.filter(stage => !stage.id);
    if (returned.length !== sent.length || created.length !== newStages.length
        || !Array.from(known).every(id => returned.some(stage => String(stage.id) === id))
        || returned.some(stage => !Number.isInteger(stage.id) || stage.id <= 0)
        || new Set(returned.map(stage => stage.id)).size !== returned.length) {
        throw new Error(t('saveError') + ': invalid saved stage identities');
    }
    let ids = persistedStageIds.get(snapshot.nodeId);
    if (!ids) { ids = new Map(); persistedStageIds.set(snapshot.nodeId, ids); }
    newStages.forEach((stage, index) => { if (stage._tmpId) ids.set(stage._tmpId, created[index].id); });
    const normalizeSnapshot = draft => {
        if (draft && draft.nodeId === snapshot.nodeId) normalizeStageIds(draft.nodeId, draft.payload.stages);
    };
    normalizeSnapshot(snapshot);
    normalizeSnapshot(nodeDrafts.get(snapshot.nodeId));
    normalizeSnapshot(pendingNodeSaves.get(snapshot.nodeId));
    queuedNodeSaves.forEach(normalizeSnapshot);
    const node = currentData.nodes[snapshot.nodeId];
    if (node) normalizeStageIds(snapshot.nodeId, node.stages);
    if (currentNodeId === snapshot.nodeId) {
        tempStages.forEach(stage => {
            const oldKey = stage._tmpId && `tmp_${stage._tmpId}`;
            normalizeStageIds(snapshot.nodeId, [stage]);
            if (oldKey && stage.id && Object.prototype.hasOwnProperty.call(expandedStages, oldKey)) {
                expandedStages[`s_${stage.id}`] = expandedStages[oldKey];
                delete expandedStages[oldKey];
            }
        });
        // Patch identities only: do not replace stages or their in-flight detail edits.
    }
}

function captureNodeSave() {
    const node = currentData.nodes[currentNodeId];
    if (!node) return null;
    const payload = {
        name: $('#field-name').val(), partCode: $('#field-partCode').val(), specs: $('#field-specs').val(),
        notes: $('#field-notes').val(),
        required_quantity: node.type === 'product' ? nonNegativeInt(node.required_quantity, 1)
            : nonNegativeInt($('#field-required_quantity').val(), 1),
        quantity: nonNegativeInt($('#field-quantity').val()),
        images: node.images || [],
        supplier: $('#field-supplier').val(),
        supplier_email: $('#field-supplier-email').val(),
        status: node.status || 'not_started'
    };
    if (node.type === 'product') payload.order_count = nonNegativeInt($('#field-order_count').val());
    if (node.type === 'part') {
        payload.partType = $('#field-partType').val();
        normalizeStageIds(currentNodeId, tempStages);
        payload.stages = tempStages.map(stage => {
            if (!stage.id) stageManufacturerIdentity(stage);
            const snapshot = { ...stage, manufacturer_ids: stageManufacturerIds(stage) };
            delete snapshot.manufacturers; // Summaries are read-only; associations persist as ordered IDs.
            return snapshot;
        });
    }
    const snapshot = { nodeId: currentNodeId, revision: ++saveRevision,
        payload: JSON.parse(JSON.stringify(payload)) };
    nodeDrafts.set(snapshot.nodeId, snapshot);
    Object.assign(node, JSON.parse(JSON.stringify(snapshot.payload)));
    refreshDemandViews();
    return snapshot;
}

function autoSaveNode() {
    const snapshot = captureNodeSave();
    if (!snapshot) return;
    pendingNodeSaves.set(snapshot.nodeId, snapshot);
    if (_autoSaveTimer) clearTimeout(_autoSaveTimer);
    $('#save-indicator').stop(true, true).text(t('saving')).fadeIn(150);
    _autoSaveTimer = setTimeout(function() {
        _autoSaveTimer = null;
        const snapshots = Array.from(pendingNodeSaves.values());
        pendingNodeSaves.clear();
        snapshots.forEach(snapshot => _doSaveNode(snapshot));
    }, 600);
}

function _doSaveNode(snapshot) {
    if (!snapshot) {
        autoSaveNode();
        return;
    }
    // Serialize writes so an older response cannot overwrite a newer edit.
    queuedNodeSaves.add(snapshot);
    saveQueue = saveQueue.then(async () => {
        normalizeStageIds(snapshot.nodeId, snapshot.payload.stages);
        const res = await fetch(`/api/node/${snapshot.nodeId}`, {
            method: 'PUT', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(snapshot.payload)
        });
        if (!res.ok) throw new Error(t('saveError') + ' HTTP ' + res.status);
        const result = await res.json();
        if (result.success === false) throw new Error(result.error || t('saveError'));
        reconcileSavedStageIds(snapshot, result.node);
        const draft = nodeDrafts.get(snapshot.nodeId);
        if (draft && draft.revision === snapshot.revision) nodeDrafts.delete(snapshot.nodeId);
        await loadData();
        loadNotifications();
        if (!nodeDrafts.size) $('#save-indicator').stop(true, true).text(t('saved')).fadeIn(150).delay(1200).fadeOut(300);
    }).catch(e => {
        // Keep the draft (including stages) available when revisiting the node or retrying.
        $('#save-indicator').stop(true, true).text(t('saveError')).fadeIn(150);
        showToast(t('saveError') + ': ' + e.message, true);
    }).finally(() => queuedNodeSaves.delete(snapshot));
    return saveQueue;
}

function bindAutoSave() {
    $('#field-name, #field-partCode, #field-specs, #field-notes, #field-order_count, #field-required_quantity, #field-quantity, #field-supplier, #field-supplier-email, #field-partType').off('.autosave').on('input.autosave change.autosave', function() {
        autoSaveNode();
    });
    $('#field-name, #field-partCode, #field-supplier, #field-supplier-email').off('.autosaveEnter').on('keypress.autosaveEnter', function(e) {
        if (e.which === 13) { e.preventDefault(); autoSaveNode(); }
    });
}

function showEditForm(node) {
    $('#no-selection').hide();
    $('#edit-form').show();
    $('#current-node').text(node.name);
    updateBreadcrumbs(currentNodeId);

    const badge = $('#node-type-badge');
    badge.removeClass('badge-product badge-assembly badge-part');
    if (node.type === 'product') badge.addClass('badge-product').text('🏭 محصول اصلی');
    else if (node.type === 'assembly') badge.addClass('badge-assembly').text(' زیرمجموعه');
    else badge.addClass('badge-part').text('⚙️ قطعه');

    $('#field-name').val(node.name);
    $('#field-partCode').val(node.partCode || '');
    $('#field-specs').val(node.specs || '');
    $('#field-notes').val(node.notes || '');
    $('#field-required_quantity').val(nonNegativeInt(node.required_quantity, 1));
    $('#field-quantity').val(node.quantity || 0);
    $('#field-supplier').val(node.supplier || '');
    $('#field-supplier-email').val(node.supplier_email || '');

    if (node.type === 'product') {
        $('#order-count-group').show();
        $('#field-order_count').val(node.order_count || 0);
    } else {
        $('#order-count-group').hide();
    }

    $('#required-quantity-group').toggle(node.type !== 'product');
    $('#field-quantity').prop('disabled', false);
    updateInventoryHelp(node);
    $('#total-required-group').show();
    $('#field-total_required').val(node.required_total);

    calculateShortage();
    renderImageGallery(node.images || []);

    const isPart = node.type === 'part';
    $('#part-email-group').toggle(isPart);

    if (isPart) {
        $('#tab-btn-mfg').show();
        $('#tab-btn-schedule').hide();
        $('#field-partType').val(node.partType || '');

        const autoStatus = inventoryStatus(node);

        $(`input[name="status"][value="${autoStatus}"]`).prop('checked', true);

        $('#field-supplier').val(node.supplier || '');
        $('#field-supplier-email').val(node.supplier_email || '');
        tempStages = JSON.parse(JSON.stringify(node.stages || []));
        tempStages.forEach(s => {
            if (!s.status) {
                s.status = s.done ? 'completed' : 'not_started';
                delete s.done;
            }
        });
        stageDetailsMap = {};
        expandedStages = {};
        renderStages();
        updateProgressBar();
        $('#tab-btn-docs').show();
        loadDocuments(currentNodeId);
        loadPartManufacturers(currentNodeId);
        loadAllManufacturers();
    } else if (node.type === 'product') {
        $('#tab-btn-mfg').hide();
        $('#tab-btn-schedule').hide();
        $('#tab-btn-docs').hide();
        $('#progress-container').hide();
    } else {
        $('#tab-btn-mfg').hide();
        $('#tab-btn-schedule').hide();
        $('#tab-btn-docs').hide();
        $('#progress-container').hide();
        if ($('.tab-btn.active').attr('onclick') === "switchTab('tab-mfg')" || $('.tab-btn.active').attr('onclick') === "switchTab('tab-schedule')") {
            switchTab('tab-general');
        }
    }
    $('#tab-btn-schedule').hide();
    if ($('#tab-schedule').hasClass('active')
        || (!isPart && ($('#tab-mfg').hasClass('active') || $('#tab-docs').hasClass('active')))) {
        switchTab('tab-general');
    }
    bindAutoSave();
}

function updateProgressBar() {
    const total = tempStages.length;
    if (total === 0) {
        $('#progress-container').hide();
        return;
    }
    $('#progress-container').show();
    const completed = tempStages.filter(s => s.status === 'completed').length;
    const percentage = Math.round((completed / total) * 100);
    $('#progress-fill').css('width', percentage + '%');
    $('#progress-percentage').text(percentage + '%');
    $('#progress-completed').text(`${completed} ` + t('completedCount'));
    $('#progress-remaining').text(`${total - completed} ` + t('remainingCount'));
}



function renderImageGallery(images) {
    const gallery = $('#image-gallery');
    gallery.empty();
    images.forEach((img, index) => {
        const url = img.url.startsWith('/') ? img.url : '/' + img.url;
        const item = $(`
            <div class="gallery-item">
                <img src="${url}" onclick="openModal('${url}')" title="${t('noImages')}">
                <div class="img-label">${img.label || t('imageLabelDefault')}</div>
                <button class="delete-img-btn" onclick="removeImage(${index})">✕</button>
            </div>
        `);
        gallery.append(item);
    });
}

function addImageToGallery(input) {
    if (input.files && input.files[0]) {
        const file = input.files[0];
        const currentInput = input;
        showPromptModal(t('imageLabel'), t('name') + ':', t('imageLabelDefault'), function(label) {
            if (label === null || label === undefined) { currentInput.value = ''; return; }
            const formData = new FormData();
            formData.append('file', file);
            fetch('/api/upload', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    const node = currentData.nodes[currentNodeId];
                    if (!node.images) node.images = [];
                    node.images.push({ url: data.url, label: label || t('imageLabelDefault') });
                    renderImageGallery(node.images);
                    currentInput.value = '';
                    autoSaveNode();
                });
        });
    }
}

function removeImage(index) {
    showConfirmModal(t('confirmDelete'), function(result) {
        if (!result) return;
        const node = currentData.nodes[currentNodeId];
        node.images.splice(index, 1);
        renderImageGallery(node.images);
        autoSaveNode();
    });
}

function openModal(src) {
    document.getElementById('modal-img').src = src;
    document.getElementById('image-modal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('image-modal').style.display = 'none';
}

function updateInventoryHelp(node) {
    const parent = currentData.nodes[node.parent];
    $('#coefficient-help').text(t('coefficientHelp') + (parent ? ': ' + parent.name : ''));
    $('#order-count-help').text(t('targetHelp'));
}

function calculateShortage() {
    const node = currentData.nodes[currentNodeId];
    if (!node) return;
    $('#field-total_required').val(node.required_total).css({
        backgroundColor: document.documentElement.dataset.theme === 'dark' ? '#242b3d' : '#f1f3f5',
        color: document.documentElement.dataset.theme === 'dark' ? '#e4e6eb' : '#333'
    });
    const missing = node.shortage > 0;
    const dark = document.documentElement.dataset.theme === 'dark';
    const feedbackColors = dark
        ? (missing ? ['#42272e', '#ffb4ab'] : ['#203b2c', '#a5dbad'])
        : (missing ? ['#ffebee', '#b42318'] : ['#e8f5e9', '#216e34']);
    $('#shortage-info').toggleClass('is-shortage', missing).toggleClass('is-sufficient', !missing).show()
        .css({ backgroundColor: feedbackColors[0], color: feedbackColors[1] });
    $('#shortage-text').css('color', feedbackColors[1])
        .text(`${t('shortage2')}: ${node.shortage} (${t('hoverTotalReq')}: ${node.required_total}, ${t('available')}: ${nonNegativeInt(node.quantity)})`);
    $(`input[name="status"][value="${inventoryStatus(node)}"]`).prop('checked', true);
}

function renderStages() {
    const list = $('#stages-list');
    list.empty();
    if (tempStages.length === 0) {
        list.html('<p style="color:var(--text-muted); margin:5px; font-size:13px;">' + t('noStages') + '</p>');
        updateProgressBar();
        updateCostSummary();
        return;
    }
    tempStages.forEach((stage, idx) => {
        const status = stage.status || 'not_started';
        const matCost = stage.estimated_material_cost || 0;
        const laborCost = stage.estimated_labor_cost || 0;
        const overhead = stage.estimated_overhead || 0;
        const hours = stage.estimated_hours || 0;
        if (!stage.id && !stage._tmpId) stage._tmpId = 'tmp_' + Date.now() + '_' + idx;
        const stageKey = stage.id ? `s_${stage.id}` : `tmp_${stage._tmpId}`;
        const isExpanded = expandedStages[stageKey] || false;

        const item = $(`
            <div class="stage-item-new" data-index="${idx}">
                <span class="stage-drag-handle" draggable="true" style="cursor: grab; color:var(--text-muted); user-select: none; -webkit-user-select: none;">☰</span>
                <div style="flex:1;min-width:0;" ondblclick="toggleStageExpand(${idx})">
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        <span class="stage-name">${escapeHtml(stage.name)}</span>
                        <button type="button" class="mfg-button" onclick="toggleStageExpand(${idx})" aria-expanded="${isExpanded}" aria-controls="stage-expanded-${idx}" style="padding:2px 6px;font-size:11px;">${currentLang === 'fa' ? 'جزئیات و سازندگان' : 'Details & manufacturers'}</button>
                        <div class="stage-status-btns">
                            <button class="stage-status-btn ${status === 'not_started' ? 'active-not-started' : ''}" onclick="setStageStatus(${idx}, 'not_started')" title="${t('notStarted')}">🔴</button>
                            <button class="stage-status-btn ${status === 'in_progress' ? 'active-in-progress' : ''}" onclick="setStageStatus(${idx}, 'in_progress')" title="${t('inProgress')}">🟡</button>
                            <button class="stage-status-btn ${status === 'completed' ? 'active-completed' : ''}" onclick="setStageStatus(${idx}, 'completed')" title="${t('completed')}">🟢</button>
                        </div>
                    </div>
                    <div style="display:flex;gap:6px;margin-top:4px;font-size:11px;color:var(--text-muted);flex-wrap:wrap;">
                        <span title="${t('material')}">💰 ${t('material')}: <input type="number" step="1000" value="${matCost}" onchange="tempStages[${idx}].estimated_material_cost=Number(this.value);updateCostSummary();autoSaveNode()" style="width:60px;padding:2px 4px;font-size:11px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);"></span>
                        <span title="${t('labor')}">🔧 ${t('labor')}: <input type="number" step="1000" value="${laborCost}" onchange="tempStages[${idx}].estimated_labor_cost=Number(this.value);updateCostSummary();autoSaveNode()" style="width:60px;padding:2px 4px;font-size:11px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);"></span>
                        <span title="${t('overhead')}">📋 ${t('overhead')}: <input type="number" step="1000" value="${overhead}" onchange="tempStages[${idx}].estimated_overhead=Number(this.value);updateCostSummary();autoSaveNode()" style="width:60px;padding:2px 4px;font-size:11px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);"></span>
                        <span title="${t('hours')}">⏱ ${t('hours')}: <input type="number" step="0.5" value="${hours}" onchange="tempStages[${idx}].estimated_hours=Number(this.value);updateCostSummary();autoSaveNode()" style="width:50px;padding:2px 4px;font-size:11px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);"></span>
                    </div>

                    ${isExpanded ? `
                    <div id="stage-expanded-${idx}" class="stage-expanded" style="margin-top:10px;padding-top:10px;border-top:1px dashed var(--border-color);">
                        <div style="background:var(--bg-tertiary);padding:8px;border-radius:6px;margin-bottom:8px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                                <strong style="font-size:12px;"> ${t('stageDetails')}</strong>
                                <button onclick="addStageDetail(${idx})" class="btn-small" style="padding:2px 8px;font-size:11px;">➕ ${t('addDetail')}</button>
                            </div>
                            <div id="stage-details-${idx}" class="stage-details-list">
                                <div style="font-size:11px;color:var(--text-muted);padding:4px;">${t('loading')}</div>
                            </div>
                        </div>
                        <div style="background:var(--bg-tertiary);padding:8px;border-radius:6px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                                <strong style="font-size:12px;">${currentLang === 'fa' ? 'سازندگان جایگزین این مرحله (به ترتیب)' : 'Stage fallback manufacturers (ordered)'}</strong>
                                <button onclick="showStageManufacturerPicker(${idx})" class="btn-small" style="padding:2px 8px;font-size:11px;">${t('addManufacturer')}</button>
                            </div>
                            <div id="stage-manufacturers-${idx}" class="manufacturers-list">
                                ${renderStageManufacturersList(stage, idx)}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>
                <button class="stage-remove-btn" onclick="removeStage(${idx})">✕</button>
            </div>
        `);
        item.on('dragstart', function(e) {
            if (!$(e.target).closest('.stage-drag-handle').length) { e.preventDefault(); return; }
            $(this).closest('.stage-item-new').addClass('dragging');
            e.originalEvent.dataTransfer.setData('text/plain', idx);
        });
        item.on('dragend', function(e) { $(this).closest('.stage-item-new').removeClass('dragging'); });
        item.on('dragover', function(e) { e.preventDefault(); });
        item.on('drop', function(e) {
            e.preventDefault();
            const fromIdx = parseInt(e.originalEvent.dataTransfer.getData('text/plain'));
            const toIdx = parseInt($(this).data('index'));
            if (fromIdx !== toIdx && !isNaN(fromIdx)) {
                // save expand/details state as arrays aligned with tempStages
                const expArr = tempStages.map((s, i) => {
                    const sk = s.id ? `s_${s.id}` : (s._tmpId ? `tmp_${s._tmpId}` : null);
                    return sk ? (expandedStages[sk] || false) : (expandedStages[i] || false);
                });
                const detArr = tempStages.map((_, i) => stageDetailsMap[i] || []);
                // reorder
                const movedItem = tempStages.splice(fromIdx, 1)[0];
                tempStages.splice(toIdx, 0, movedItem);
                const movedExp = expArr.splice(fromIdx, 1)[0];
                expArr.splice(toIdx, 0, movedExp);
                const movedDet = detArr.splice(fromIdx, 1)[0];
                detArr.splice(toIdx, 0, movedDet);
                // rebuild maps using stageKey
                expandedStages = {};
                stageDetailsMap = {};
                tempStages.forEach((s, i) => {
                    if (!s.id && !s._tmpId) s._tmpId = 'tmp_' + Date.now() + '_' + i;
                    const sk = s.id ? `s_${s.id}` : `tmp_${s._tmpId}`;
                    if (expArr[i]) expandedStages[sk] = true;
                    if (detArr[i].length) stageDetailsMap[i] = detArr[i]; // keep numeric for simplicity
                });
                renderStages();
                autoSaveNode();
            }
        });
        list.append(item);

        if (isExpanded) {
            loadStageDetails(idx, stage);
        }
    });
    updateProgressBar();
    updateCostSummary();
}

function toggleStageExpand(idx) {
    const stage = tempStages[idx];
    if (!stage) return;
    if (!stage.id && !stage._tmpId) stage._tmpId = 'tmp_' + Date.now() + '_' + idx;
    const stageKey = stage.id ? `s_${stage.id}` : `tmp_${stage._tmpId}`;
    expandedStages[stageKey] = !expandedStages[stageKey];
    renderStages();
}

// ───── Stage Details ─────

function loadStageDetails(idx, stage) {
    const container = $(`#stage-details-${idx}`);
    if (!container.length) return;
    if (stage.id && stage.id.toString().startsWith('s_')) {
        stage.id = parseInt(stage.id.toString().replace('s_', ''));
    }
    if (stage.id && typeof stage.id === 'number') {
        fetch(`/api/v2/stages/${stage.id}/details`)
            .then(res => res.json())
            .then(res => {
                if (res.success) {
                    stageDetailsMap[idx] = res.data;
                    renderStageDetails(idx);
                }
            });
    } else {
        stageDetailsMap[idx] = stageDetailsMap[idx] || [];
        renderStageDetails(idx);
    }
}

function renderStageDetails(idx) {
    const container = $(`#stage-details-${idx}`);
    if (!container.length) return;
    const details = stageDetailsMap[idx] || [];
    if (details.length === 0) {
        container.html('<div style="font-size:11px;color:var(--text-muted);padding:4px;">' + t('noStages') + '. ' + t('addDetail') + '.</div>');
        return;
    }
    let html = '';
    details.forEach((d, di) => {
        html += `
            <div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:4px;padding:4px;background:var(--bg-secondary);border-radius:4px;">
                <span style="font-weight:bold;font-size:12px;min-width:18px;">${d.step_number || (di+1)}.</span>
                <span style="flex:1;font-size:12px;">${escapeHtml(d.description)}</span>
                <button onclick="editStageDetail(${idx}, ${di})" class="btn-small" style="padding:1px 6px;font-size:10px;">✏️</button>
                <button onclick="removeStageDetail(${idx}, ${di})" class="btn-small" style="padding:1px 6px;font-size:10px;background:#f44336;">✕</button>
            </div>
        `;
    });
    container.html(html);
}

function addStageDetail(idx) {
    window._detailStageIdx = idx;
    window._detailEditIdx = -1;
    $('#detail-modal-title').text(t('stageDetails') + ' - ' + t('addDetail'));
    $('#detail-desc').val('');
    $('#detail-modal').fadeIn(150);
}

function editStageDetail(idx, di) {
    const details = stageDetailsMap[idx] || [];
    const d = details[di];
    if (!d) return;
    window._detailStageIdx = idx;
    window._detailEditIdx = di;
    $('#detail-modal-title').text(t('stageDetails') + ' - ' + t('edit'));
    $('#detail-desc').val(d.description);
    $('#detail-modal').fadeIn(150);
}

function closeDetailModal() {
    $('#detail-modal').fadeOut(150);
    window._detailStageIdx = null;
    window._detailEditIdx = null;
}

function submitDetailForm() {
    const idx = window._detailStageIdx;
    const editDi = window._detailEditIdx;
    const desc = $('#detail-desc').val().trim();
    if (!desc) { showAlertModal(t('detailText')); return; }
    const details = stageDetailsMap[idx] = stageDetailsMap[idx] || [];
    if (editDi >= 0 && editDi < details.length) {
        // Edit existing
        const d = details[editDi];
        d.description = desc;
        if (d.id) {
            fetch(`/api/v2/stage-details/${d.id}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ description: desc, step_number: d.step_number })
            });
        }
        renderStageDetails(idx);
    } else {
        // New
        const stepNum = details.length + 1;
        details.push({ step_number: stepNum, description: desc });
        const stage = tempStages[idx];
        if (stage && stage.id && typeof stage.id === 'number') {
            fetch('/api/v2/stage-details', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ stage_id: stage.id, step_number: stepNum, description: desc })
            }).then(res => res.json()).then(r => {
                if (r.success) details[details.length-1] = r.data;
                renderStageDetails(idx);
            });
        } else {
            renderStageDetails(idx);
        }
    }
    closeDetailModal();
}

function removeStageDetail(idx, di) {
    showConfirmModal(t('delete') + '?', function(result) {
        if (!result) return;
        const details = stageDetailsMap[idx] || [];
        const d = details[di];
        if (d && d.id) {
            fetch(`/api/v2/stage-details/${d.id}`, { method: 'DELETE' });
        }
        details.splice(di, 1);
        details.forEach((dt, i) => dt.step_number = i + 1);
        renderStageDetails(idx);
    });
}

// Stage associations use only the classic node autosave payload, never a stage PUT.
function stageManufacturerIds(stage) {
    const source = Array.isArray(stage.manufacturer_ids) ? stage.manufacturer_ids
        : (Array.isArray(stage.manufacturers) ? stage.manufacturers.map(m => m.id) : []);
    return Array.from(new Set(source.map(Number).filter(id => Number.isInteger(id) && id > 0)));
}

function stageManufacturerIdentity(stage) {
    if (stage.id) return 'id:' + String(stage.id).replace(/^s_/, '');
    if (!stage._tmpId) stage._tmpId = 'mfr_' + Date.now() + '_' + Math.random().toString(36).slice(2);
    return 'tmp:' + stage._tmpId;
}

function resolveManufacturerStage(context) {
    if (!context || context.nodeId !== currentNodeId) return null;
    const index = tempStages.findIndex(stage => stageManufacturerIdentity(stage) === context.stageKey
        || (stage._tmpId && 'tmp:' + stage._tmpId === context.stageKey));
    return index < 0 ? null : { stage: tempStages[index], index };
}

function renderStageManufacturersList(stage, idx) {
    const ids = stageManufacturerIds(stage);
    if (!ids.length) return '<p class="mfg-hint">' + t('noManufacturer') + '</p>';
    return ids.map((id, order) => {
        const m = allManufacturers.find(m => Number(m.id) === id)
            || (stage.manufacturers || []).find(m => Number(m.id) === id) || { id, name: '#' + id };
        const inactive = !ManufacturerUI.isActive(m);
        return `<div class="mfg-stage-row"><strong dir="auto">${order + 1}. ${ManufacturerUI.esc(m.name)}</strong>
            ${inactive ? '<span class="mfg-chip mfg-inactive">' + ManufacturerUI.tr('inactive') + '</span>' : ''}
            ${ManufacturerUI.summary(m)}
            <div class="mfg-actions">
                <button type="button" class="mfg-button" onclick="moveStageManufacturer(${idx},${order},-1)" ${order === 0 ? 'disabled' : ''} aria-label="${currentLang === 'fa' ? 'بالا' : 'Move up'}">↑</button>
                <button type="button" class="mfg-button" onclick="moveStageManufacturer(${idx},${order},1)" ${order === ids.length - 1 ? 'disabled' : ''} aria-label="${currentLang === 'fa' ? 'پایین' : 'Move down'}">↓</button>
                <button type="button" class="mfg-button" onclick="removeStageManufacturer(${idx},${order})">${t('delete')}</button>
            </div></div>`;
    }).join('');
}

function refreshStageManufacturerLists() {
    tempStages.forEach((stage, idx) => {
        const container = document.getElementById('stage-manufacturers-' + idx);
        if (container) container.innerHTML = renderStageManufacturersList(stage, idx);
    });
}

function moveStageManufacturer(idx, order, direction) {
    const stage = tempStages[idx]; if (!stage) return;
    const ids = stageManufacturerIds(stage); const next = order + direction;
    if (next < 0 || next >= ids.length || ![-1, 1].includes(direction)) return;
    [ids[order], ids[next]] = [ids[next], ids[order]];
    stage.manufacturer_ids = ids; refreshStageManufacturerLists(); autoSaveNode();
}

function removeStageManufacturer(idx, order) {
    const stage = tempStages[idx]; if (!stage) return;
    const ids = stageManufacturerIds(stage); if (order < 0 || order >= ids.length) return;
    ids.splice(order, 1); stage.manufacturer_ids = ids; refreshStageManufacturerLists(); autoSaveNode();
}

function addStageManufacturer(context, manufacturer) {
    const target = resolveManufacturerStage(context);
    const id = Number(manufacturer && manufacturer.id);
    if (!target || !Number.isInteger(id) || id <= 0) return false;
    const ids = stageManufacturerIds(target.stage); if (ids.includes(id)) return false;
    target.stage.manufacturer_ids = [...ids, id];
    allManufacturers = allManufacturers.filter(m => Number(m.id) !== id).concat(manufacturer);
    refreshStageManufacturerLists(); autoSaveNode(); return true;
}

function showStageManufacturerPicker(idx) {
    const stage = tempStages[idx]; if (!stage) return;
    const context = { nodeId: currentNodeId, stageKey: stageManufacturerIdentity(stage) };
    const ui = ManufacturerUI; const view = ui.modal(t('selectManufacturer') + ' — ' + stage.name);
    const filters = document.createElement('div'); filters.className = 'mfg-picker-filters';
    const search = document.createElement('input'); search.type = 'search'; search.placeholder = ui.tr('search'); search.setAttribute('aria-label', ui.tr('search'));
    const active = document.createElement('select'); active.setAttribute('aria-label', ui.tr('active'));
    active.add(new Option(ui.tr('active'), 'true')); active.add(new Option(ui.tr('all'), 'all')); active.add(new Option(ui.tr('inactive'), 'false'));
    const category = document.createElement('select'); category.setAttribute('aria-label', ui.tr('category'));
    const tags = document.createElement('div'); const metadataError = document.createElement('div');
    const hint = document.createElement('p'); hint.className = 'mfg-hint'; hint.textContent = ui.tr('tagHint');
    filters.append(search, active, category, tags, hint, metadataError); view.card.append(filters);
    const status = document.createElement('div'); status.setAttribute('aria-live', 'polite'); const results = document.createElement('div'); results.className = 'mfg-picker-results'; view.card.append(status, results);
    let revision = 0; let timer;
    function valid() { return view.overlay.isConnected && !!resolveManufacturerStage(context); }
    async function reload() {
        if (!valid()) { view.close(); return; }
        const own = ++revision; status.className = 'mfg-message'; status.textContent = ui.tr('loading'); results.replaceChildren();
        try {
            const data = await ui.list('/manufacturers?' + ui.query({ q: search.value, active: active.value, category_id: category.value, tag_ids: ui.selectedTags(tags) }));
            if (!valid() || own !== revision) return;
            const target = resolveManufacturerStage(context); const ids = stageManufacturerIds(target.stage);
            const available = data.filter(m => !ids.includes(Number(m.id)) && (active.value !== 'true' || ui.isActive(m)));
            status.textContent = available.length ? '' : ui.tr('empty');
            available.forEach(m => {
                const row = document.createElement('div'); row.className = 'mfg-picker-result';
                row.innerHTML = `<strong dir="auto">${ui.esc(m.name)}</strong> ${!ui.isActive(m) ? '<span class="mfg-chip mfg-inactive">' + ui.tr('inactive') + '</span>' : ''}${ui.summary(m)}`;
                const add = document.createElement('button'); add.type = 'button'; add.className = 'mfg-button'; add.textContent = t('add');
                add.onclick = () => { if (valid() && addStageManufacturer(context, m)) reload(); }; row.append(add); results.append(row);
            });
        } catch (error) { if (valid() && own === revision) ui.errorMessage(status, error, reload); }
    }
    async function metadata() {
        try { await ui.loadMetadata(); if (!valid()) return; ui.categoryOptions(category, ui.tr('anyCategory')); ui.tagChoices(tags, []); metadataError.replaceChildren(); }
        catch (error) { if (valid()) ui.errorMessage(metadataError, error, metadata); }
    }
    search.oninput = () => { clearTimeout(timer); timer = setTimeout(reload, 250); };
    active.onchange = reload; category.onchange = reload; tags.onchange = reload;
    const create = document.createElement('button'); create.type = 'button'; create.className = 'mfg-button mfg-primary'; create.textContent = t('createManufacturer');
    create.onclick = () => {
        if (!valid()) { view.close(); return; }
        ui.openEditor(null, m => {
            if (!valid()) return;
            if (m && m.id) allManufacturers = allManufacturers.filter(item => Number(item.id) !== Number(m.id)).concat(m);
            reload(); // Return to the picker; creating does not automatically attach or route.
        });
    };
    const directory = document.createElement('a'); directory.href = '/manufacturers'; directory.target = '_blank'; directory.rel = 'noopener'; directory.className = 'mfg-button'; directory.textContent = ui.tr('title');
    view.card.append(create, directory); metadata(); reload(); search.focus();
}

// ───── Standalone part manufacturers (kept separate) ─────

function loadPartManufacturers(partId) {
    partManufacturers = [];
    refreshManufacturersList();
    const pid = parseInt(partId.toString().replace(/^[a-z]/, ''));
    if (isNaN(pid)) return;
    fetch(`/api/v2/parts/${pid}/manufacturers`)
        .then(res => res.json())
        .then(res => {
            if (res.success && partId === currentNodeId && Array.isArray(res.data)) {
                partManufacturers = res.data;
                refreshManufacturersList();
            }
        }).catch(e => console.error('loadPartManufacturers error:', e));
}

let manufacturerLoadRevision = 0;
function loadAllManufacturers() {
    const revision = ++manufacturerLoadRevision;
    return ManufacturerUI.list('/manufacturers?active=all').then(data => {
        if (revision !== manufacturerLoadRevision) return;
        allManufacturers = data;
        refreshStageManufacturerLists();
    }).catch(error => {
        showToast(ManufacturerUI.tr('failed') + ' ' + error.message, true);
    });
}

function renderPartManufacturersList() {
    if (!partManufacturers || partManufacturers.length === 0) {
        return '<div style="font-size:11px;color:var(--text-muted);padding:4px;">' + t('noManufacturer') + '</div>';
    }
    let html = '';
    partManufacturers.forEach((m, mi) => {
        html += `
            <div class="manufacturer-item" style="margin-bottom:4px;border:1px solid var(--border-color);border-radius:4px;overflow:hidden;">
                <div class="mfr-header" onclick="toggleMfrExpand(${mi})" style="display:flex;justify-content:space-between;align-items:center;padding:6px 8px;cursor:pointer;background:var(--bg-secondary);font-size:12px;font-weight:bold;">
                    <span>${mfrExpandState[mi] ? '▼' : '▶'} ${escapeHtml(m.name)}</span>
                    <button onclick="event.stopPropagation();removeManufacturerFromPart(${mi})" class="btn-small" style="padding:1px 6px;font-size:10px;background:#f44336;">✕</button>
                </div>
                <div class="mfr-body" style="${mfrExpandState[mi] ? 'display:block;' : 'display:none;'}padding:8px;font-size:11px;">
                    ${renderManufacturerInfo(m)}
                </div>
            </div>
        `;
    });
    return html;
}

let mfrExpandState = {};

function refreshManufacturersList() {
    const container = $('#part-manufacturers-list');
    if (container.length) {
        container.html(renderPartManufacturersList());
    }
}

function toggleMfrExpand(mi) {
    mfrExpandState[mi] = !mfrExpandState[mi];
    refreshManufacturersList();
}

function renderManufacturerInfo(m) {
    let html = '';
    if (m.emails && m.emails.length) {
        m.emails.forEach(e => {
            html += `<div style="margin-bottom:2px;">📧 ${t('mfrEmail')}: ${escapeHtml(e.email)}</div>`;
        });
    }
    if (m.phones && m.phones.length) {
        m.phones.forEach(p => {
            html += `<div style="margin-bottom:2px;">📞 ${t('mfrPhone')}: ${escapeHtml(p.phone)}</div>`;
        });
    }
    if (m.socials && m.socials.length) {
        m.socials.forEach(s => {
            html += `<div style="margin-bottom:2px;">🌐 ${escapeHtml(s.platform)}: ${escapeHtml(s.handle)}</div>`;
        });
    }
    if (m.address) {
        html += `<div style="margin-bottom:2px;">📍 ${t('mfrAddress')}: ${escapeHtml(m.address)}</div>`;
    }
    if (m.notes) {
        html += `<div style="margin-bottom:2px;">📝 ${t('mfrNotes')}: ${escapeHtml(m.notes)}</div>`;
    }
    if (!html) html = '<div style="color:var(--text-muted);">' + t('mfrInfo') + '</div>';
    return html;
}

function showAddManufacturerToPart() {
    const nodeId = currentNodeId;
    const unused = allManufacturers.filter(m => ManufacturerUI.isActive(m)
        && !partManufacturers.some(pm => Number(pm.id) === Number(m.id)));
    const listContainer = $('#mfr-select-list');
    listContainer.empty();
    if (unused.length === 0) {
        listContainer.text(t('allAdded'));
    } else {
        unused.forEach(m => {
            const row = document.createElement('button'); row.type = 'button'; row.className = 'select-item';
            row.innerHTML = `<div class="select-item-name">${ManufacturerUI.esc(m.name)}</div>${ManufacturerUI.summary(m)}`;
            row.onclick = () => { if (nodeId === currentNodeId) addManufacturerToPart(m.id); closeMfrSelectModal(); };
            listContainer.append(row);
        });
    }
    $('#mfr-select-modal').fadeIn(150);
}

function closeMfrSelectModal() {
    $('#mfr-select-modal').fadeOut(150);
}

function showCreateManufacturerForm() {
    const nodeId = currentNodeId;
    ManufacturerUI.openEditor(null, () => {
        loadAllManufacturers().then(() => {
            if (currentNodeId === nodeId) showAddManufacturerToPart();
        });
    });
}

function closeMfrFormModal() {
    $('#mfr-form-modal').fadeOut(150);
}

function addMfrEmailRow() {
    $('#mfr-emails-container').append(`
        <div class="modal-multi-row">
            <input type="email" class="mfr-email-input" placeholder="example@company.com">
            <button onclick="this.parentElement.remove()" class="btn-small" style="padding:1px 6px;font-size:10px;background:#f44336;">✕</button>
        </div>
    `);
}

function addMfrSocialRow() {
    $('#mfr-socials-container').append(`
        <div class="modal-multi-row">
            <input type="text" class="mfr-social-platform" placeholder="پلتفرم (Telegram, Instagram...)" style="width:40%;">
            <input type="text" class="mfr-social-handle" placeholder="آیدی (@username)" style="width:55%;">
            <button onclick="this.parentElement.remove()" class="btn-small" style="padding:1px 6px;font-size:10px;background:#f44336;">✕</button>
        </div>
    `);
}

function submitMfrForm() {
    const name = $('#mfr-name').val().trim();
    if (!name) { showAlertModal(t('nameRequired')); return; }
    const phone = $('#mfr-phone').val().trim();
    const address = $('#mfr-address').val().trim();
    const notes = $('#mfr-notes').val().trim();
    const emails = [];
    $('.mfr-email-input').each(function() {
        const v = $(this).val().trim();
        if (v) emails.push({ email: v });
    });
    const socials = [];
    $('.mfr-social-platform').each(function(i) {
        const platform = $(this).val().trim();
        const handle = $('.mfr-social-handle').eq(i).val().trim();
        if (platform && handle) socials.push({ platform, handle });
    });
    const payload = { name, phone, address, notes, emails, socials };
    if (window._editingMfrId) {
        fetch(`/api/v2/manufacturers/${window._editingMfrId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(r => {
            if (r.success) {
                closeMfrFormModal();
                loadAllManufacturers();
                loadPartManufacturers(currentNodeId);
            } else {
                showAlertModal('خطا: ' + (r.error || 'نامشخص'));
            }
        }).catch(e => showAlertModal('خطا: ' + e.message));
    } else {
        fetch('/api/v2/manufacturers', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(r => {
            if (r.success) {
                allManufacturers.push(r.data);
                closeMfrFormModal();
                showAddManufacturerToPart();
            } else {
                showAlertModal('خطا در ایجاد سازنده: ' + (r.error || 'نامشخص'));
            }
        }).catch(e => showAlertModal('خطا در ارتباط با سرور: ' + e.message));
    }
}

function addManufacturerToPart(mfrId) {
    const nodeId = currentNodeId;
    const pid = parseInt(nodeId.toString().replace(/^[a-z]/, ''));
    if (isNaN(pid)) { showAlertModal('خطا: قطعه شناسه معتبری ندارد'); return; }
    fetch(`/api/v2/parts/${pid}/manufacturers`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ manufacturer_id: mfrId })
    }).then(res => res.json()).then(r => {
        if (r.success) {
            if (nodeId !== currentNodeId) return;
            partManufacturers.push(r.data);
            refreshManufacturersList();
        } else {
            showAlertModal('خطا: ' + (r.error || 'نامشخص'));
        }
    }).catch(e => {
        showAlertModal('خطا در ارتباط با سرور: ' + e.message);
    });
}

function removeManufacturerFromPart(mi) {
    const nodeId = currentNodeId;
    const mfr = partManufacturers[mi]; if (!mfr) return;
    showConfirmModal(t('delete') + ' "' + mfr.name + '"?', function(result) {
        if (!result || nodeId !== currentNodeId) return;
        const pid = parseInt(nodeId.toString().replace(/^[a-z]/, ''));
        if (isNaN(pid)) return;
        fetch(`/api/v2/parts/${pid}/manufacturers/${mfr.id}`, { method: 'DELETE' })
            .then(res => res.json()).then(r => {
                if (r.success) {
                    if (nodeId !== currentNodeId) return;
                    const index = partManufacturers.findIndex(item => Number(item.id) === Number(mfr.id));
                    if (index >= 0) partManufacturers.splice(index, 1);
                    mfrExpandState[mi] = false;
                    refreshManufacturersList();
                } else {
                    showAlertModal('خطا: ' + (r.error || 'نامشخص'));
                }
            }).catch(e => {
                showAlertModal('خطا در ارتباط با سرور: ' + e.message);
            });
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function updateCostSummary() {
    const totalMat = tempStages.reduce((s, st) => s + (st.estimated_material_cost || 0), 0);
    const totalLabor = tempStages.reduce((s, st) => s + (st.estimated_labor_cost || 0), 0);
    const totalOverhead = tempStages.reduce((s, st) => s + (st.estimated_overhead || 0), 0);
    const totalHours = tempStages.reduce((s, st) => s + (st.estimated_hours || 0), 0);
    const grandTotal = totalMat + totalLabor + totalOverhead;
    if (grandTotal > 0) {
        $('#cost-summary-group').show();
        $('#cost-summary').html(
            `<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:5px;">
                <span>${t('materialCost')}: <strong>${totalMat.toLocaleString()}</strong></span>
                <span>${t('laborCost')}: <strong>${totalLabor.toLocaleString()}</strong></span>
                <span>${t('overheadCost')}: <strong>${totalOverhead.toLocaleString()}</strong></span>
                <span>${t('estimatedHours')}: <strong>${totalHours}</strong></span>
                <span style="color:var(--accent-green);font-weight:bold;">${t('total')}: ${grandTotal.toLocaleString()}</span>
            </div>`
        );
    } else {
        $('#cost-summary-group').hide();
    }
}

function setStageStatus(idx, status) {
    tempStages[idx].status = status;
    renderStages();
    autoSaveNode();
}

function addStage() {
    const name = $('#new-stage-name').val().trim();
    if (!name) { showAlertModal(t('stageRequired')); return; }
    tempStages.push({ name: name, status: 'not_started', estimated_material_cost: 0, estimated_labor_cost: 0, estimated_overhead: 0, estimated_hours: 0 });
    $('#new-stage-name').val('');
    renderStages();
    autoSaveNode();
}

function removeStage(idx) {
    showConfirmModal(t('delete') + ' "' + tempStages[idx].name + '"؟', function(ok) {
        if (!ok) return;
        tempStages.splice(idx, 1);
        renderStages();
        autoSaveNode();
    });
}

// Inline Edit
function openInlineEdit(nodeId, field, currentValue) {
    inlineEditContext = { nodeId, field };
    $('#inline-edit-title').text(t('edit') + ' ' + (field === 'name' ? t('name') : t('specs')));
    $('#inline-edit-input').val(currentValue);
    $('#inline-edit-modal').show();
    $('#inline-edit-input').focus();
}

function confirmInlineEdit() {
    if (!inlineEditContext) return;
    const value = $('#inline-edit-input').val().trim();
    if (!value) { cancelInlineEdit(); return; }

    const payload = {};
    payload[inlineEditContext.field] = value;

    fetch(`/api/node/${inlineEditContext.nodeId}`, {
        method: 'PATCH',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).then(() => {
        cancelInlineEdit();
        loadData();
    });
}

function cancelInlineEdit() {
    inlineEditContext = null;
    $('#inline-edit-modal').hide();
}

function addRootProduct() {
    showPromptModal('محصول جدید', 'نام محصول:', '', function(name) {
        if (!name) return;
        fetch('/api/node', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: name, type: 'product', parent: null }) }).then(() => loadData());
    });
}

function addChildOf(type) {
    if (!currentNodeId) { showAlertModal(t('selectNode')); return; }
    const parentNode = currentData.nodes[currentNodeId];
    if (parentNode.type === 'part') { showAlertModal(t('partNoChildren')); return; }
    const typeKey = type === 'assembly' ? 'newAssembly' : 'newPart';
    showPromptModal(t(typeKey), t('name') + ':', t(typeKey), function(name) {
        if (!name) return;
        fetch('/api/node', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: name, type: type, parent: currentNodeId }) })
        .then(res => res.json()).then(result => {
            if (result.success) {
                if (!openedNodes.includes(currentNodeId)) openedNodes.push(currentNodeId);
                loadData();
            }
        });
    });
}

function deleteNode() {
    if (!currentNodeId) return;
    showConfirmModal(t('confirmDelete'), function(result) {
        if (!result) return;
        fetch(`/api/node/${currentNodeId}`, { method: 'DELETE' }).then(() => {
            currentNodeId = null;
            $('#edit-form').hide();
            $('#no-selection').show();
            $('#breadcrumbs').hide();
            loadData();
        });
    });
}

function saveNode() {
    autoSaveNode();
}

function exportExcel() {
    const products = [];
    Object.values(currentData.nodes).forEach(node => {
        if (node.type === 'product') products.push({ id: node.id, name: node.name, order_count: node.order_count || 0 });
    });
    if (products.length === 0) { showAlertModal(t('noProduct')); return; }
    showProductSelectModal(t('productForExport'), products, function(pid) {
        window.location.href = `/api/export/excel?product_id=${pid}`;
    });
}

function exportSchematic() {
    const products = [];
    Object.values(currentData.nodes).forEach(node => {
        if (node.type === 'product') products.push({ id: node.id, name: node.name });
    });
    if (products.length === 0) { showAlertModal(t('noProduct')); return; }
    showProductSelectModal(t('productForExport'), products, function(pid) {
        window.location.href = `/api/export/schematic?product_id=${pid}`;
    });
}

// Dark Mode
function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const newTheme = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    $('#theme-toggle').text(theme === 'dark' ? '☀️' : '🌙');
}

// ───── Email & Documents ─────

function sendPartEmail() {
    const email = $('#field-supplier-email').val().trim();
    if (!email) { showAlertModal(t('supplierEmail')); return; }
    showConfirmModal(t('sendEmail') + ` ${t('supplier')}: ${email}?`, function(result) {
        if (!result) return;
        fetch('/api/send-part-email', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ part_id: currentNodeId, email: email })
        })
        .then(res => res.json())
        .then(r => { showAlertModal(r.message || 'ارسال شد'); })
        .catch(e => { showAlertModal('خطا در ارسال: ' + e.message); });
    });
}

function loadDocuments(nodeId) {
    fetch(`/api/documents/${nodeId}`)
        .then(res => res.json())
        .then(res => {
            if (!res.success) return;
            const container = $('#documents-list');
            container.empty();
            if (!res.data || res.data.length === 0) {
                container.html('<div style="color:var(--text-muted);padding:10px;font-size:13px;">' + t('noDocuments') + '</div>');
                return;
            }
            res.data.forEach(doc => {
                const iconMap = { pdf: '📄', cad: '🔩', doc: '📝', xls: '📊', image: '🖼', archive: '📦', other: '📁' };
                const icon = iconMap[doc.file_type] || iconMap.other;
                const sizeStr = doc.file_size > 1024*1024 ? (doc.file_size/1024/1024).toFixed(1)+' MB' : (doc.file_size/1024).toFixed(0)+' KB';
                container.append(`
                    <div style="display:flex;align-items:center;gap:10px;padding:10px;background:var(--bg-tertiary);border-radius:6px;margin-bottom:6px;border:1px solid var(--border-color);">
                        <span style="font-size:20px;">${icon}</span>
                        <div style="flex:1;min-width:0;">
                            <div style="font-weight:bold;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${doc.filename}</div>
                            <div style="font-size:11px;color:var(--text-muted);">${sizeStr} | ${new Date(doc.uploaded_at).toLocaleDateString('fa-IR')}</div>
                        </div>
                        <a href="${doc.url}" target="_blank" class="btn-small" style="text-decoration:none;background:#4CAF50;">⬇ ${t('download')}</a>
                        <button onclick="deleteDocument(${doc.id})" class="btn-small" style="background:#f44336;">✕</button>
                    </div>
                `);
            });
        });
}

function uploadDocument(input) {
    if (!input.files || !input.files[0]) return;
    const file = input.files[0];
    const formData = new FormData();
    formData.append('file', file);
    fetch(`/api/documents/upload/${currentNodeId}`, {
        method: 'POST', body: formData
    })
    .then(res => res.json())
    .then(r => {
        if (r.success) { input.value = ''; loadDocuments(currentNodeId); }
        else { showAlertModal(r.error || 'خطا در بارگذاری'); }
    })
    .catch(e => { showAlertModal('خطا: ' + e.message); });
}

function deleteDocument(docId) {
    showConfirmModal(t('confirmDelete'), function(result) {
        if (!result) return;
        fetch(`/api/documents/${docId}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(r => { if (r.success) loadDocuments(currentNodeId); });
    });
}

// ───── Production Scheduling ─────

function loadSchedulesForProduct(nodeId) {
    const node = currentData.nodes[nodeId];
    if (!node || node.type !== 'product') {
        $('#tab-btn-schedule').hide();
        return;
    }
    fetch('/api/schedules')
        .then(res => res.json())
        .then(res => {
            if (!res.success) return;
            const container = $('#schedule-list');
            container.empty();
            const productName = node.name;
            let productId = nodeId;
            const schedules = res.data.filter(s => s.product_name === productName || s.product_id == productId.replace('p',''));
            if (schedules.length === 0) {
                container.html('<div style="color:var(--text-muted);padding:10px;">' + t('noSchedules') + '</div>');
                return;
            }
            const statusMap = { planned: t('planned'), in_progress: t('inProgress'), completed: t('completed'), cancelled: t('cancelled') };
            schedules.forEach(s => {
                container.append(`
                    <div style="background:var(--bg-tertiary);padding:10px;border-radius:6px;margin-bottom:8px;border-right:3px solid ${s.status === 'completed' ? '#4CAF50' : s.status === 'in_progress' ? '#FF9800' : '#9E9E9E'};">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <strong>${s.quantity} ${t('orderCount')}</strong>
                            <span style="font-size:12px;padding:2px 8px;border-radius:10px;background:${s.status === 'completed' ? '#4CAF50' : s.status === 'in_progress' ? '#FF9800' : '#9E9E9E'};color:#fff;">${statusMap[s.status] || s.status}</span>
                        </div>
                        <div style="font-size:12px;color:var(--text-muted);margin-top:5px;">
                            ${t('priority')}: ${s.priority} | ${t('start')}: ${s.start_date ? new Date(s.start_date).toLocaleDateString(currentLang === 'fa' ? 'fa-IR' : 'en-US') : '-'} | ${t('end')}: ${s.end_date ? new Date(s.end_date).toLocaleDateString(currentLang === 'fa' ? 'fa-IR' : 'en-US') : '-'}
                        </div>
                        ${s.notes ? '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">' + s.notes + '</div>' : ''}
                    </div>
                `);
            });
        });
}

function showAddSchedule() {
    const node = currentData.nodes[currentNodeId];
    if (!node || node.type !== 'product') { showAlertModal(t('selectNode')); return; }
    showScheduleModal();
}

// Collapsible Panels
function togglePanel(panel) {
    if (panel === 'tree') {
        $('#tree-panel').toggleClass('collapsed');
        $('#tree-panel .collapse-btn').text($('#tree-panel').hasClass('collapsed') ? '▶' : '◀');
    } else if (panel === 'edit') {
        $('#edit-panel').toggleClass('collapsed');
        $('#edit-panel .collapse-btn').text($('#edit-panel').hasClass('collapsed') ? '' : '▶');
    }
}

// ───── Generic Prompt Modal ─────
window._promptCallback = null;

function showPromptModal(title, label, defaultValue, callback) {
    $('#prompt-modal-title').text(title);
    $('#prompt-modal-label').text(label);
    $('#prompt-modal-input').val(defaultValue || '');
    window._promptCallback = callback;
    $('#prompt-modal').fadeIn(150);
    setTimeout(() => $('#prompt-modal-input').focus(), 200);
}

function submitPromptModal() {
    const val = $('#prompt-modal-input').val().trim();
    if (window._promptCallback) window._promptCallback(val);
    window._promptCallback = null;
    $('#prompt-modal').fadeOut(150);
}

function closePromptModal() {
    window._promptCallback = null;
    $('#prompt-modal').fadeOut(150);
}

// ───── Generic Confirm Modal ─────
window._confirmCallback = null;

function showConfirmModal(message, callback) {
    $('#confirm-modal-message').text(message);
    window._confirmCallback = callback;
    $('#confirm-modal').fadeIn(150);
}

function submitConfirmModal(result) {
    if (window._confirmCallback) window._confirmCallback(result);
    window._confirmCallback = null;
    $('#confirm-modal').fadeOut(150);
}

function closeConfirmModal() {
    window._confirmCallback = null;
    $('#confirm-modal').fadeOut(150);
}

// ───── Generic Alert Modal ─────
function showAlertModal(message) {
    $('#alert-modal-message').text(message);
    $('#alert-modal').fadeIn(150);
}

function closeAlertModal() {
    $('#alert-modal').fadeOut(150);
}

// ───── Product Select Modal ─────
window._productSelectCallback = null;

function showProductSelectModal(title, products, callback) {
    $('#product-select-title').text(title);
    const list = $('#product-select-list');
    list.empty();
    if (!products || products.length === 0) {
        list.html('<div style="padding:20px;text-align:center;color:var(--text-muted);">' + t('noProduct') + '</div>');
    } else {
        products.forEach((p, i) => {
            list.append(`
                <div class="select-item" data-pid="${p.id}">
                    <div class="select-item-name">${escapeHtml(p.name)}</div>
                    <div class="select-item-info">${p.order_count ? p.order_count + ' ' + t('order') : ''}</div>
                </div>
            `);
        });
        list.find('.select-item').on('click', function() {
            const pid = $(this).data('pid');
            if (window._productSelectCallback) window._productSelectCallback(pid);
            window._productSelectCallback = null;
            $('#product-select-modal').fadeOut(150);
        });
    }
    window._productSelectCallback = callback;
    $('#product-select-modal').fadeIn(150);
}

function closeProductSelectModal() {
    window._productSelectCallback = null;
    $('#product-select-modal').fadeOut(150);
}

// ───── Toast Notification ─────
function showToast(message, isError) {
    $('.toast').remove();
    const toast = $(`<div class="toast" style="background:${isError ? 'var(--accent-red)' : 'var(--accent-green)'};"></div>`);
    toast.text((isError ? '✕ ' : '✅ ') + message);
    $('body').append(toast);
    setTimeout(() => toast.remove(), 2500);
}

// ───── Schedule Modal ─────
function showScheduleModal() {
    $('#sched-quantity').val(1);
    $('#sched-start').val('');
    $('#sched-end').val('');
    $('#sched-notes').val('');
    $('#schedule-modal').fadeIn(150);
}

function submitScheduleModal() {
    const quantity = parseInt($('#sched-quantity').val()) || 1;
    const startDate = $('#sched-start').val();
    const endDate = $('#sched-end').val();
    const notes = $('#sched-notes').val().trim();

    const node = currentData.nodes[currentNodeId];
    if (!node || node.type !== 'product') { showAlertModal(t('selectNode')); return; }

    const productId = parseInt(currentNodeId.toString().replace(/^[a-z]/, ''));
    fetch('/api/schedules', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity,
            start_date: startDate ? startDate + 'T00:00:00' : null,
            end_date: endDate ? endDate + 'T23:59:59' : null,
            notes: notes
        })
    }).then(res => res.json()).then(() => {
        $('#schedule-modal').fadeOut(150);
        showToast(t('newSchedule') + ' ' + t('saveSuccess'));
        loadSchedulesForProduct(currentNodeId);
    }).catch(e => showAlertModal('خطا: ' + e.message));
}

function closeScheduleModal() {
    $('#schedule-modal').fadeOut(150);
}

// Keyboard shortcut for notifications
$(document).on('keydown', function(e) {
    if (e.key === 'n' && e.ctrlKey) {
        e.preventDefault();
        toggleNotifications();
    }
    if (e.key === 'Escape') {
        $('#notification-panel').slideUp(200);
        cancelInlineEdit();
    }
});