let currentNodeId = null;
let currentData = { nodes: {}, root_ids: [] };
let tempStages = [];
let openedNodes = [];
let currentView = 'tree';
let currentMainView = 'tree';
let inlineEditContext = null;
let stageDetailsMap = {};
let allManufacturers = [];
let expandedStages = {};
let _autoSaveTimer = null;

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
        requiredQuantity: 'تعداد مورد نیاز',
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
        manufacturers: 'سازنده‌ها',
        addManufacturer: 'افزودن سازنده',
        noManufacturer: 'هیچ سازنده‌ای ثبت نشده',
        createManufacturer: 'ایجاد سازنده جدید',
        editManufacturer: 'ویرایش سازنده',
        deleteManufacturer: 'حذف سازنده',
        selectManufacturer: 'انتخاب سازنده',
        none: 'بدون',
        manageManufacturers: 'مدیریت سازنده‌ها',
        manufacturer: 'سازنده',
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
        orderCount: 'تعداد سفارش',
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
        // PLM
        versions: 'نسخه‌ها',
        changeRequests: 'درخواست تغییر',
        noVersions: 'هیچ نسخه‌ای ثبت نشده',
        noChangeRequests: 'هیچ درخواست تغییر ثبت نشده',
        createVersion: 'ایجاد نسخه جدید',
        versionNumber: 'شماره نسخه',
        changeSummary: 'خلاصه تغییرات',
        versionCreated: 'نسخه با موفقیت ایجاد شد',
        activateVersion: 'فعال‌سازی',
        versionActivated: 'نسخه فعال شد',
        changeRequest: 'درخواست تغییر',
        createChangeRequest: 'ایجاد درخواست تغییر',
        description: 'توضیحات',
        justification: 'موجبات/استدلال',
        submitChangeRequest: 'ثبت درخواست',
        changeRequestSubmitted: 'درخواست تغییر ثبت شد',
        pending: 'در انتظار بررسی',
        approved: 'تأیید شده',
        rejected: 'رد شده',
        voteApprove: 'تأیید',
        voteReject: 'رد',
        voteSubmitted: 'رأی شما ثبت شد',
        alreadyVoted: 'شما قبلاً در این درخواست رأی داده‌اید',
        reviewChangeRequest: 'بررسی درخواست',
        approve: 'تأیید',
        reject: 'رد',
        reviewed: 'بررسی شده',
        requestedBy: 'درخواست‌کننده',
        requestedAt: 'زمان درخواست',
        reviewAt: 'زمان بررسی',
        status: 'وضعیت',
        votes: 'رأی‌ها',
        approveCount: 'تأیید',
        rejectCount: 'رد',
        vote: 'رأی',
        version: 'نسخه',
        activeVersion: 'نسخه فعال',
        created: 'تاریخ ایجاد',
        details: 'جزئیات',
        changeRequestDetails: 'جزئیات درخواست تغییر',
        partType: 'نوع قطعه',
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
        requiredQuantity: 'Required Qty',
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
        manufacturers: 'Manufacturers',
        addManufacturer: 'Add Manufacturer',
        noManufacturer: 'No manufacturer registered',
        createManufacturer: 'Create New Manufacturer',
        editManufacturer: 'Edit Manufacturer',
        deleteManufacturer: 'Delete Manufacturer',
        selectManufacturer: 'Select Manufacturer',
        none: 'None',
        manageManufacturers: 'Manage Manufacturers',
        manufacturer: 'Manufacturer',
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
        orderCount: 'Order Count',
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
        // PLM
        versions: 'Versions',
        changeRequests: 'Change Requests',
        noVersions: 'No versions recorded',
        noChangeRequests: 'No change requests',
        createVersion: 'Create New Version',
        versionNumber: 'Version Number',
        changeSummary: 'Change Summary',
        versionCreated: 'Version created successfully',
        activateVersion: 'Activate',
        versionActivated: 'Version activated',
        changeRequest: 'Change Request',
        createChangeRequest: 'Create Change Request',
        description: 'Description',
        justification: 'Justification',
        submitChangeRequest: 'Submit Request',
        changeRequestSubmitted: 'Change request submitted',
        pending: 'Pending Review',
        approved: 'Approved',
        rejected: 'Rejected',
        voteApprove: 'Approve',
        voteReject: 'Reject',
        voteSubmitted: 'Your vote has been recorded',
        alreadyVoted: 'You have already voted on this request',
        reviewChangeRequest: 'Review Request',
        approve: 'Approve',
        reject: 'Reject',
        reviewed: 'Reviewed',
        requestedBy: 'Requested By',
        requestedAt: 'Requested At',
        reviewAt: 'Reviewed At',
        status: 'Status',
        votes: 'Votes',
        approveCount: 'Approve',
        rejectCount: 'Reject',
        vote: 'Vote',
        version: 'Version',
        activeVersion: 'Active Version',
        created: 'Created',
        details: 'Details',
        changeRequestDetails: 'Change Request Details',
        partType: 'Part Type',
    }
};

let currentLang = localStorage.getItem('appLang') || 'fa';

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
    $('#tab-btn-plm-changes').text('🔄 ' + t('changeRequests'));
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
    $('#stat-total-label').text(t('product'));
    $('#stat-done-label').text(t('completedCount'));
    $('#stat-missing-label').text(t('shortage'));
    $('#plm-changes-label').text(t('changeRequests') + ':');
    $('#plm-new-cr-title').text(t('submitChangeRequest'));
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
    const savedLang = localStorage.getItem('appLang') || 'fa';
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

    const savedOpened = localStorage.getItem('openedNodes');
    if (savedOpened) openedNodes = JSON.parse(savedOpened);

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

function loadData() {
    fetch('/api/data')
        .then(res => res.json())
        .then(data => {
            currentData = data;
            updateStageSuggestions();
            updateDashboard();
            if (currentMainView === 'tree') renderTree();
            else if (currentMainView === 'kanban') renderKanban();
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
                            <span style="color:#d32f2f;">${t('shortage2')}: ${item.shortage}</span>
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

function getAncestorOrderCount(nodeId) {
    let node = currentData.nodes[nodeId];
    while (node) {
        if (node.type === 'product' && node.order_count > 0) return node.order_count;
        if (node.parent) node = currentData.nodes[node.parent];
        else break;
    }
    return 1;
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
        if (node.type === 'part') {
            total++;
            if (node.status === 'completed') done++;
            const orderCount = getAncestorOrderCount(node.id);
            const totalReq = (node.required_quantity || 1) * orderCount;
            if ((node.quantity || 0) < totalReq) missing++;
        }
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
            openInlineEdit(node.id, 'name', node.text.replace(/^[^\s]+\s/, ''));
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

    if (node.type === 'part') {
        const orderCount = getAncestorOrderCount(nodeId);
        const totalReq = (node.required_quantity || 1) * orderCount;
        const available = node.quantity || 0;
        stockText = t('hoverStock') + ': ' + available + ' / ' + t('hoverTotalReq') + ': ' + totalReq;

        if (available >= totalReq) {
            statusText = t('hoverSufficient');
            statusColor = '#4CAF50';
        } else if (available > 0) {
            statusText = t('hoverPartial');
            statusColor = '#FF9800';
        } else {
            statusText = '🔴 ' + t('hoverShortage');
            statusColor = '#F44336';
        }
    } else {
        stockText = t('hoverType') + ': ' + (node.type === 'product' ? t('product') : t('assembly'));
        statusText = '';
    }

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
        const orderCount = getAncestorOrderCount(nodeId);
        const totalRequired = (node.required_quantity || 1) * orderCount;
        const available = node.quantity || 0;

        if (available >= totalRequired) { color = '#4CAF50'; text += ' 🟢'; }
        else if (available > 0) { color = '#FF9800'; text += ' 🟡'; }
        else { color = '#F44336'; text += ' 🔴'; }

        if (node.partType === 'buy') text = '🛒 ' + text;
        else if (node.partType === 'make') text = '🔧 ' + text;
        else text = '⚙️ ' + text;
    }

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
        if (node.type === 'part') {
            const orderCount = getAncestorOrderCount(node.id);
            const totalReq = (node.required_quantity || 1) * orderCount;
            const available = node.quantity || 0;
            let status = 'not_started';
            if (available >= totalReq) status = 'completed';
            else if (available > 0) status = 'in_progress';

            columns[status].cards.push({
                id: node.id, name: node.name,
                code: node.partCode || '-',
                required: totalReq, available: available,
                stages: node.stages ? node.stages.length : 0
            });
        }
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
                <div class="kanban-card status-${status}" onclick="goToNode('${card.id}')">
                    <div class="kanban-card-name">${card.name}</div>
                    <div class="kanban-card-info">${t('code')}: ${card.code}</div>
                    <div class="kanban-card-info">${t('hoverStock')}: ${card.available} / ${card.required}</div>
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

function autoSaveNode() {
    if (_autoSaveTimer) clearTimeout(_autoSaveTimer);
    $('#save-indicator').text('⏳').fadeIn(150);
    _autoSaveTimer = setTimeout(function() {
        _autoSaveTimer = null;
        _doSaveNode();
    }, 600);
}

function _doSaveNode() {
    if (!currentNodeId) return;
    const node = currentData.nodes[currentNodeId];
    if (!node) return;
    const updatedData = {
        name: $('#field-name').val(), partCode: $('#field-partCode').val(), specs: $('#field-specs').val(),
        notes: $('#field-notes').val(),
        required_quantity: parseInt($('#field-required_quantity').val()) || 1,
        quantity: parseInt($('#field-quantity').val()) || 0,
        images: node.images || [],
        supplier: $('#field-supplier').val(),
        supplier_email: $('#field-supplier-email').val(),
        status: node.status || 'not_started'
    };
    if (node.type === 'product') {
        updatedData.order_count = parseInt($('#field-order_count').val()) || 0;
    }
    if (node.type === 'part') {
        updatedData.partType = $('#field-partType').val();
        updatedData.stages = tempStages;
        // ── Phase 1+2: PERT / cost / resource fields ──
        const toFloat = (v) => { const n = parseFloat(v); return isNaN(n) ? null : n; };
        const hasStagePert = tempStages.some(s => s.time_optimistic != null);
        if (hasStagePert) {
            // Stages carry PERT/cost → don't overwrite Part-level fields
            updatedData.time_optimistic = null;
            updatedData.time_most_likely = null;
            updatedData.time_pessimistic = null;
            updatedData.cost_material = null;
            updatedData.cost_labor = null;
            updatedData.cost_overhead = null;
            updatedData.required_resource_type = null;
            updatedData.storage_cost_per_day = null;
        } else {
            updatedData.time_optimistic = toFloat($('#field-time_optimistic').val());
            updatedData.time_most_likely = toFloat($('#field-time_most_likely').val());
            updatedData.time_pessimistic = toFloat($('#field-time_pessimistic').val());
            updatedData.cost_material = toFloat($('#field-cost_material').val());
            updatedData.cost_labor = toFloat($('#field-cost_labor').val());
            updatedData.cost_overhead = toFloat($('#field-cost_overhead').val());
            updatedData.required_resource_type = $('#field-required_resource_type').val() || null;
            updatedData.storage_cost_per_day = toFloat($('#field-storage_cost_per_day').val());
        }
    }
    fetch(`/api/node/${currentNodeId}`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(updatedData) })
    .then(() => {
        loadData();
        $('#save-indicator').text('✅').fadeIn(150).delay(1200).fadeOut(300);
    })
    .catch(e => {
        $('#save-indicator').text('❌').fadeIn(150).delay(1500).fadeOut(300);
        showToast('خطا در ذخیره: ' + e.message, true);
    });
}

function bindAutoSave() {
    $('#field-name, #field-partCode, #field-specs, #field-notes, #field-order_count, #field-required_quantity, #field-quantity, #field-supplier, #field-supplier-email, #field-partType').off('.autosave').on('change.autosave keyup.autosave', function() {
        autoSaveNode();
    });
    // Phase 1: PERT / cost / resource fields
    $('#field-time_optimistic, #field-time_most_likely, #field-time_pessimistic, #field-cost_material, #field-cost_labor, #field-cost_overhead, #field-storage_cost_per_day, #field-required_resource_type').off('.autosave').on('change.autosave keyup.autosave', function() {
        updatePertDisplay();
        updateCostDisplay();
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
    $('#field-required_quantity').val(node.required_quantity || 1);
    $('#field-quantity').val(node.quantity || 0);

    if (node.type === 'product') {
        $('#order-count-group').show();
        $('#field-order_count').val(node.order_count || 0);
    } else {
        $('#order-count-group').hide();
    }

    if (node.type === 'part') {
        const orderCount = getAncestorOrderCount(currentNodeId);
        const totalRequired = (node.required_quantity || 1) * orderCount;
        $('#total-required-group').show();
        $('#field-total_required').val(totalRequired);
    } else {
        $('#total-required-group').hide();
    }

    calculateShortage();
    renderImageGallery(node.images || []);

    const isPart = node.type === 'part';
    $('#part-email-group').toggle(isPart);

    if (isPart) {
        $('#tab-btn-mfg').show();
        $('#tab-btn-schedule').hide();
        $('#tab-btn-pert').show();
        $('#field-partType').val(node.partType || '');
        // ── Phase 1+2: populate PERT / cost / resource fields ──
        const hasStages = node.stages && node.stages.length > 0 && node.stages.some(s => s.time_optimistic != null);
        if (hasStages) {
            // Stages exist → show computed values as read-only
            $('#field-time_optimistic').val('').prop('readonly', true).css('background', '#f0f0f0');
            $('#field-time_most_likely').val('').prop('readonly', true).css('background', '#f0f0f0');
            $('#field-time_pessimistic').val('').prop('readonly', true).css('background', '#f0f0f0');
            $('#field-cost_material').val('').prop('readonly', true).css('background', '#f0f0f0');
            $('#field-cost_labor').val('').prop('readonly', true).css('background', '#f0f0f0');
            $('#field-cost_overhead').val('').prop('readonly', true).css('background', '#f0f0f0');
            $('#field-required_resource_type').prop('disabled', true).css('background', '#f0f0f0');
            $('#field-storage_cost_per_day').val('').prop('readonly', true).css('background', '#f0f0f0');
            // Show computed PERT
            if (node.pert_expected_time != null) {
                $('#pert-expected').html('<strong>زمان مورد انتظار (مجموع مراحل):</strong> ' + node.pert_expected_time.toFixed(1) + ' ساعت');
                $('#pert-stddev').html('<strong>انحراف معیار (مجموع مراحل):</strong> ' + (node.pert_std_dev || 0).toFixed(1) + ' ساعت');
                $('#pert-result').show();
            }
            // Show computed cost
            if (node.total_direct_cost > 0) {
                $('#cost-direct-total').html('<strong>هزینه مستقیم کل (مجموع مراحل):</strong> ' + node.total_direct_cost.toLocaleString('fa-IR') + ' ریال');
                $('#cost-direct-result').show();
            }
            $('#pert-computed-note').show();
        } else {
            // No stages → editable fields
            $('#field-time_optimistic').val(node.time_optimistic ?? '').prop('readonly', false).css('background', '');
            $('#field-time_most_likely').val(node.time_most_likely ?? '').prop('readonly', false).css('background', '');
            $('#field-time_pessimistic').val(node.time_pessimistic ?? '').prop('readonly', false).css('background', '');
            $('#field-cost_material').val(node.cost_material ?? '').prop('readonly', false).css('background', '');
            $('#field-cost_labor').val(node.cost_labor ?? '').prop('readonly', false).css('background', '');
            $('#field-cost_overhead').val(node.cost_overhead ?? '').prop('readonly', false).css('background', '');
            $('#field-required_resource_type').prop('disabled', false).css('background', '');
            $('#field-storage_cost_per_day').val(node.storage_cost_per_day ?? '').prop('readonly', false).css('background', '');
            updatePertDisplay();
            updateCostDisplay();
            $('#pert-computed-note').hide();
        }

        const required = parseInt(node.required_quantity) || 1;
        const available = parseInt(node.quantity) || 0;
        const orderCount = getAncestorOrderCount(currentNodeId);
        const totalReq = required * orderCount;
        const autoStatus = available >= totalReq ? 'completed' : (available > 0 ? 'in_progress' : 'not_started');
        node.status = autoStatus;

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
        loadAllManufacturers();
    } else if (node.type === 'product') {
        $('#tab-btn-mfg').hide();
        $('#tab-btn-schedule').show();
        $('#tab-btn-pert').hide();
        $('#tab-btn-docs').hide();
        $('#tab-btn-plm-changes').hide();
        loadSchedulesForProduct(currentNodeId);
    } else {
        $('#tab-btn-mfg').hide();
        $('#tab-btn-schedule').hide();
        $('#tab-btn-pert').hide();
        $('#tab-btn-docs').hide();
        $('#tab-btn-plm-changes').hide();
        $('#progress-container').hide();
        if ($('.tab-btn.active').attr('onclick') === "switchTab('tab-mfg')" || $('.tab-btn.active').attr('onclick') === "switchTab('tab-schedule')") {
            switchTab('tab-general');
        }
    }
    bindAutoSave();
}

// ── Phase 1: PERT & Cost display helpers ──

function updatePertDisplay() {
    const o = parseFloat($('#field-time_optimistic').val());
    const m = parseFloat($('#field-time_most_likely').val());
    const p = parseFloat($('#field-time_pessimistic').val());
    if (!isNaN(o) && !isNaN(m) && !isNaN(p) && o <= m && m <= p) {
        const expected = (o + 4 * m + p) / 6;
        const stddev = (p - o) / 6;
        $('#pert-expected').html('<strong>زمان مورد انتظار:</strong> ' + expected.toFixed(1) + ' ساعت');
        $('#pert-stddev').html('<strong>انحراف معیار:</strong> ' + stddev.toFixed(1) + ' ساعت');
        $('#pert-result').show();
    } else {
        $('#pert-result').hide();
    }
}

function updateCostDisplay() {
    const mat = parseFloat($('#field-cost_material').val()) || 0;
    const lab = parseFloat($('#field-cost_labor').val()) || 0;
    const ovh = parseFloat($('#field-cost_overhead').val()) || 0;
    const total = mat + lab + ovh;
    if (total > 0) {
        $('#cost-direct-total').html('<strong>هزینه مستقیم کل:</strong> ' + total.toLocaleString('fa-IR') + ' ریال');
        $('#cost-direct-result').show();
    } else {
        $('#cost-direct-result').hide();
    }
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

function calculateShortage() {
    const node = currentData.nodes[currentNodeId];
    if (!node) return;
    const orderCount = getAncestorOrderCount(currentNodeId);
    const required = (parseInt(node.required_quantity) || 1) * orderCount;
    const available = parseInt(node.quantity) || 0;
    const shortage = required - available;
    const infoDiv = $('#shortage-info');
    const textSpan = $('#shortage-text');
    if (shortage > 0) {
        infoDiv.show(); infoDiv.css('background', '#ffebee');
        textSpan.html(`<strong>${shortage}</strong> ${t('shortage2')}! (${t('hoverTotalReq')}: ${required}, ${t('available')}: ${available})`);
        textSpan.css('color', '#d32f2f');
    } else if (shortage === 0) {
        infoDiv.show(); infoDiv.css('background', '#e8f5e9');
        textSpan.html('🟢 ' + t('hoverSufficient'));
        textSpan.css('color', '#2e7d32');
    } else {
        infoDiv.show(); infoDiv.css('background', '#e3f2fd');
        textSpan.html(`<strong>${Math.abs(shortage)}</strong>`);
        textSpan.css('color', '#1976d2');
    }
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
                        <span class="stage-name">${stage.name}</span>
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
                    <div class="stage-expanded" style="margin-top:10px;padding-top:10px;border-top:1px dashed var(--border-color);">
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
                            <strong style="font-size:12px;">🏭 ${t('manufacturer')}</strong>
                            <div style="display:flex;gap:8px;margin-top:6px;align-items:center;">
                                <select onchange="setStageManufacturer(${idx}, this.value)" style="flex:1;min-width:0;padding:4px 6px;font-size:12px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);">
                                    <option value="">— ${t('none')} —</option>
                                    ${allManufacturers.map(m => `<option value="${m.id}" ${Number(stage.manufacturer_id) === Number(m.id) ? 'selected' : ''}>${escapeHtml(m.name)}</option>`).join('')}
                                </select>
                                <button onclick="showManufacturersManager()" class="btn-small" style="padding:2px 8px;font-size:11px;white-space:nowrap;">⚙ ${t('manageManufacturers')}</button>
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
// ───── Manufacturers ─────

function loadAllManufacturers() {
    fetch('/api/v2/manufacturers')
        .then(res => res.json())
        .then(res => {
            if (res.success) {
                allManufacturers = res.data;
                if (typeof tempStages !== 'undefined' && tempStages.length) renderStages();
            }
        });
}

function setStageManufacturer(idx, val) {
    if (!tempStages[idx]) return;
    tempStages[idx].manufacturer_id = val ? Number(val) : null;
    autoSaveNode();
}

function showManufacturersManager() {
    renderManufacturersManagerList();
    $('#mfr-manager-modal').fadeIn(150);
}

function closeMfrManagerModal() {
    $('#mfr-manager-modal').fadeOut(150);
}

function renderManufacturersManagerList() {
    const container = $('#mfr-manager-list');
    if (!container.length) return;
    container.empty();
    if (!allManufacturers || allManufacturers.length === 0) {
        container.html('<div style="padding:20px;text-align:center;color:var(--text-muted);">' + t('noManufacturer') + '</div>');
        return;
    }
    allManufacturers.forEach(m => {
        const info = [];
        if (m.emails && m.emails.length) info.push('\u2709\ufe0f ' + m.emails[0].email);
        if (m.phones && m.phones.length) info.push('\u260e\ufe0f ' + m.phones[0].phone);
        container.append(`
            <div class="manufacturer-item" style="margin-bottom:6px;border:1px solid var(--border-color);border-radius:6px;padding:8px;display:flex;justify-content:space-between;align-items:center;">
                <div style="min-width:0;">
                    <div style="font-size:13px;font-weight:bold;">${escapeHtml(m.name)}</div>
                    <div style="font-size:11px;color:var(--text-muted);margin-top:2px;">${info.join(' | ') || t('mfrInfo')}</div>
                </div>
                <div style="display:flex;gap:6px;white-space:nowrap;">
                    <button onclick="editManufacturer(${m.id})" class="btn-small" style="background:#2196F3;">\u270f\ufe0f ${t('edit')}</button>
                    <button onclick="deleteManufacturer(${m.id})" class="btn-small" style="background:#f44336;">\ud83d\uddd1 ${t('delete')}</button>
                </div>
            </div>
        `);
    });
}

function editManufacturer(id) {
    const m = allManufacturers.find(x => x.id === id);
    if (!m) return;
    window._editingMfrId = id;
    $('#mfr-form-title').text(t('editManufacturer'));
    $('#mfr-name').val(m.name || '');
    $('#mfr-phone').val((m.phones && m.phones[0]) ? m.phones[0].phone : '');
    $('#mfr-address').val(m.address || '');
    $('#mfr-notes').val(m.notes || '');
    const emails = (m.emails || []);
    $('#mfr-emails-container').html(emails.length ? emails.map(e => `
        <div class="modal-multi-row">
            <input type="email" class="mfr-email-input" value="${escapeHtml(e.email)}">
            <button onclick="this.parentElement.remove()" class="btn-small" style="padding:1px 6px;font-size:10px;background:#f44336;">\u2715</button>
        </div>`).join('') : `
        <div class="modal-multi-row">
            <input type="email" class="mfr-email-input" placeholder="example@company.com">
        </div>`);
    const socials = (m.socials || []);
    $('#mfr-socials-container').html(socials.length ? socials.map(s => `
        <div class="modal-multi-row">
            <input type="text" class="mfr-social-platform" value="${escapeHtml(s.platform)}" placeholder="\u067e\u0644\u062a\u0641\u0631\u0645" style="width:40%;">
            <input type="text" class="mfr-social-handle" value="${escapeHtml(s.handle)}" placeholder="\u0622\u06cc\u062f\u06cc" style="width:55%;">
        </div>`).join('') : `
        <div class="modal-multi-row">
            <input type="text" class="mfr-social-platform" placeholder="\u067e\u0644\u062a\u0641\u0631\u0645 (Telegram, Instagram, ...)" style="width:40%;">
            <input type="text" class="mfr-social-handle" placeholder="\u0622\u06cc\u062f\u06cc (@username)" style="width:55%;">
        </div>`);
    $('#mfr-form-modal').fadeIn(150);
}

function deleteManufacturer(id) {
    const m = allManufacturers.find(x => x.id === id);
    showConfirmModal(t('delete') + ' "' + (m ? m.name : '') + '"?', function(result) {
        if (!result) return;
        fetch(`/api/v2/manufacturers/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(r => {
                if (r.success) {
                    loadAllManufacturers();
                    renderManufacturersManagerList();
                } else {
                    showToast('\u062e\u0637\u0627: ' + (r.error || '\u0646\u0627\u0645\u0634\u062e\u0635'), true);
                }
            })
            .catch(e => showToast('\u062e\u0637\u0627 \u062f\u0631 \u0627\u0631\u062a\u0628\u0627\u0637 \u0628\u0627 \u0633\u0631\u0648\u0631: ' + e.message, true));
    });
}

function showCreateManufacturerForm() {
    $('#mfr-form-title').text(t('createManufacturer'));
    $('#mfr-name').val('');
    $('#mfr-phone').val('');
    $('#mfr-address').val('');
    $('#mfr-notes').val('');
    $('#mfr-emails-container').html(`
        <div class="modal-multi-row">
            <input type="email" class="mfr-email-input" placeholder="example@company.com">
        </div>
    `);
    $('#mfr-socials-container').html(`
        <div class="modal-multi-row">
            <input type="text" class="mfr-social-platform" placeholder="\u067e\u0644\u062a\u0641\u0631\u0645 (Telegram, Instagram, ...)" style="width:40%;">
            <input type="text" class="mfr-social-handle" placeholder="\u0622\u06cc\u062f\u06cc (@username)" style="width:55%;">
        </div>
    `);
    window._editingMfrId = null;
    $('#mfr-form-modal').fadeIn(150);
}

function closeMfrFormModal() {
    $('#mfr-form-modal').fadeOut(150);
}

function addMfrEmailRow() {
    $('#mfr-emails-container').append(`
        <div class="modal-multi-row">
            <input type="email" class="mfr-email-input" placeholder="example@company.com">
            <button onclick="this.parentElement.remove()" class="btn-small" style="padding:1px 6px;font-size:10px;background:#f44336;">\u2715</button>
        </div>
    `);
}

function addMfrSocialRow() {
    $('#mfr-socials-container').append(`
        <div class="modal-multi-row">
            <input type="text" class="mfr-social-platform" placeholder="\u067e\u0644\u062a\u0641\u0631\u0645 (Telegram, Instagram...)" style="width:40%;">
            <input type="text" class="mfr-social-handle" placeholder="\u0622\u06cc\u062f\u06cc (@username)" style="width:55%;">
            <button onclick="this.parentElement.remove()" class="btn-small" style="padding:1px 6px;font-size:10px;background:#f44336;">\u2715</button>
        </div>
    `);
}

function submitMfrForm() {
    const name = $('#mfr-name').val().trim();
    if (!name) { showToast(t('nameRequired'), true); return; }
    const phone = $('#mfr-phone').val().trim();
    const address = $('#mfr-address').val().trim();
    const notes = $('#mfr-notes').val().trim();
    const emails = [];
    $('#mfr-emails-container .mfr-email-input').each(function() {
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
                renderManufacturersManagerList();
            } else {
                showToast('\u062e\u0637\u0627: ' + (r.error || '\u0646\u0627\u0645\u0634\u062e\u0635'), true);
            }
        }).catch(e => showToast('\u062e\u0637\u0627: ' + e.message, true));
    } else {
        fetch('/api/v2/manufacturers', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        }).then(res => res.json()).then(r => {
            if (r.success) {
                allManufacturers.push(r.data);
                closeMfrFormModal();
                renderManufacturersManagerList();
            } else {
                showToast('\u062e\u0637\u0627 \u062f\u0631 \u0627\u06cc\u062c\u0627\u062f \u0633\u0627\u0632\u0646\u062f\u0647: ' + (r.error || '\u0646\u0627\u0645\u0634\u062e\u0635'), true);
            }
        }).catch(e => showToast('\u062e\u0637\u0627 \u062f\u0631 \u0627\u0631\u062a\u0628\u0627\u0637 \u0628\u0627 \u0633\u0631\u0648\u0631: ' + e.message, true));
    }
}

function renderManufacturerInfo(m) {
    let html = '';
    if (m.emails && m.emails.length) {
        m.emails.forEach(e => {
            html += `<div style="margin-bottom:2px;">\u2709\ufe0f ${t('mfrEmail')}: ${escapeHtml(e.email)}</div>`;
        });
    }
    if (m.phones && m.phones.length) {
        m.phones.forEach(p => {
            html += `<div style="margin-bottom:2px;">\u260e\ufe0f ${t('mfrPhone')}: ${escapeHtml(p.phone)}</div>`;
        });
    }
    if (m.socials && m.socials.length) {
        m.socials.forEach(s => {
            html += `<div style="margin-bottom:2px;">\ud83c\udf10 ${escapeHtml(s.platform)}: ${escapeHtml(s.handle)}</div>`;
        });
    }
    if (m.address) {
        html += `<div style="margin-bottom:2px;">\ud83d\udccd ${t('mfrAddress')}: ${escapeHtml(m.address)}</div>`;
    }
    if (m.notes) {
        html += `<div style="margin-bottom:2px;">\ud83d\udcdd ${t('mfrNotes')}: ${escapeHtml(m.notes)}</div>`;
    }
    if (!html) html = '<div style="color:var(--text-muted);">' + t('mfrInfo') + '</div>';
    return html;
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

// ───── PLM: Change Requests ─────

function loadChangeRequests(nodeId) {
    const partId = nodeId.replace('r', '');
    fetch(`/api/v2/parts/${partId}/change-requests`)
        .then(res => res.json())
        .then(res => {
            const container = $('#plm-changes-list');
            container.empty();
            if (!res.success || !res.data || res.data.length === 0) {
                container.html('<div style="color:var(--text-muted);padding:10px;font-size:13px;">' + t('noChangeRequests') + '</div>');
                return;
            }
            res.data.forEach(cr => {
                const statusMap = { pending: t('pending'), approved: t('approved'), rejected: t('rejected') };
                const statusColors = { pending: '#FF9800', approved: '#4CAF50', rejected: '#f44336' };
                const statusColor = statusColors[cr.status] || '#9E9E9E';
                const canVote = cr.status === 'pending' && currentUser && !cr.votes.some(v => v.user_id === currentUser.id);
                container.append(`
                    <div style="display:flex;flex-direction:column;gap:8px;padding:12px;background:var(--bg-tertiary);border-radius:6px;margin-bottom:8px;border:1px solid var(--border-color);border-right:4px solid ${statusColor};">
                        <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                            <div style="flex:1;">
                                <div style="display:flex;align-items:center;gap:8px;font-weight:bold;font-size:13px;">
                                    <span>#${cr.id}</span>
                                    <span style="font-size:11px;padding:2px 8px;border-radius:4px;background:${statusColor};color:#fff;">${statusMap[cr.status] || cr.status}</span>
                                </div>
                                <div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">${cr.description}</div>
                                ${cr.justification ? `<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">${t('justification')}: ${cr.justification}</div>` : ''}
                                <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">
                                    ${t('requestedBy')}: ${cr.requester_name} | ${t('created')}: ${new Date(cr.created_at).toLocaleString('fa-IR')}
                                </div>
                            </div>
                        </div>
                        <div style="display:flex;gap:8px;flex-wrap:wrap;">
                            ${cr.status === 'pending' && canVote ? `
                                <button onclick="voteChangeRequest(${cr.id}, 'approve')" class="btn-small" style="background:#4CAF50;">✅ ${t('approve')}</button>
                                <button onclick="voteChangeRequest(${cr.id}, 'reject')" class="btn-small" style="background:#f44336;">❌ ${t('reject')}</button>
                            ` : cr.status !== 'pending' ? `
                                <span style="font-size:11px;padding:4px 10px;border-radius:4px;background:${statusColor};color:#fff;">${statusMap[cr.status]}</span>
                            ` : ''}
                            <button onclick="showChangeRequestDetails(${cr.id})" class="btn-small" style="background:#2196F3;">${t('details')}</button>
                        </div>
                        ${cr.votes && cr.votes.length > 0 ? `
                            <div style="font-size:11px;color:var(--text-muted);border-top:1px solid var(--border-color);padding-top:8px;margin-top:4px;">
                                ${t('votes')}: ${cr.votes.filter(v => v.vote_type === 'approve').length} ✅ | ${cr.votes.filter(v => v.vote_type === 'reject').length} ❌
                            </div>
                        ` : ''}
                    </div>
                `);
            });
        });
}

function createChangeRequest() {
    const partId = currentNodeId.replace('r', '');
    const description = ($('#plm-cr-description').val() || '').trim();
    if (!description) { showToast(t('error') + ': ' + t('description'), true); return; }
    const justification = ($('#plm-cr-justification').val() || '').trim();
    fetch(`/api/v2/parts/${partId}/change-requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: description, justification: justification })
    })
    .then(res => res.json())
    .then(r => {
        if (r.success) {
            $('#plm-cr-description').val('');
            $('#plm-cr-justification').val('');
            loadChangeRequests(currentNodeId);
            showToast(t('changeRequestSubmitted'));
        } else {
            showToast(r.error || t('error'), true);
        }
    })
    .catch(e => showToast(t('error') + ': ' + e.message, true));
}

function voteChangeRequest(crId, voteType) {
    showConfirmModal(t('confirm') + ' ' + voteType + '?', function(result) {
        if (!result) return;
        fetch(`/api/v2/change-requests/${crId}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ vote_type: voteType })
        })
        .then(res => res.json())
        .then(r => {
            if (r.success) {
                loadChangeRequests(currentNodeId);
                showToast(t('voteSubmitted'));
            } else {
                showToast(r.error || t('error'), true);
            }
        })
        .catch(e => showToast(t('error') + ': ' + e.message, true));
    });
}

function showChangeRequestDetails(crId) {
    fetch(`/api/v2/change-requests/${crId}`)
        .then(res => res.json())
        .then(r => {
            if (!r.success) return;
            const cr = r.data;
            const statusMap = { pending: t('pending'), approved: t('approved'), rejected: t('rejected') };
            const statusColors = { pending: '#FF9800', approved: '#4CAF50', rejected: '#f44336' };
            const statusColor = statusColors[cr.status] || '#9E9E9E';
            showAlertModal(`
                <div style="font-size:13px;line-height:1.7;">
                    <strong>#${cr.id} - ${statusMap[cr.status] || cr.status}</strong>
                    <div style="margin:8px 0;padding:8px;background:var(--bg-tertiary);border-radius:4px;">
                        <strong>${t('description')}:</strong> ${cr.description}
                    </div>
                    ${cr.justification ? `<div style="margin:8px 0;padding:8px;background:var(--bg-tertiary);border-radius:4px;"><strong>${t('justification')}:</strong> ${cr.justification}</div>` : ''}
                    <div style="font-size:12px;color:var(--text-muted);">
                        ${t('requestedBy')}: ${cr.requester_name}<br>
                        ${t('created')}: ${new Date(cr.created_at).toLocaleString('fa-IR')}<br>
                        ${cr.reviewed_at ? `${t('reviewed')}: ${new Date(cr.reviewed_at).toLocaleString('fa-IR')}` : ''}
                    </div>
                    ${cr.votes && cr.votes.length > 0 ? `
                        <div style="margin-top:10px;padding-top:10px;border-top:1px solid var(--border-color);">
                            <strong>${t('votes')}:</strong>
                            <div style="font-size:12px;margin-top:4px;">
                                ${cr.votes.map(v => `<span style="margin-left:10px;">${v.voter_name}: ${v.vote_type === 'approve' ? '✅' : '❌'}</span>`).join('<br>')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `, { title: t('changeRequestDetails') });
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
    $('#alert-modal-message').html(message);
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
    const toast = $(`<div class="toast" style="background:${isError ? 'var(--accent-red)' : 'var(--accent-green)'};">${isError ? '✕' : '✅'} ${message}</div>`);
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