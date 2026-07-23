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
    $('#field-partType-label').text(t('type'));
    $('#btn-add-assembly').text('📦 ' + t('newAssembly'));
    $('#btn-add-part').text('⚙️ ' + t('newPart'));
    $('#btn-delete').innerHTML = '️ ' + t('delete');
    $('#add-image-label').text(t('images'));
    $('#add-doc-label').text(t('techDocs'));
    $('#part-email-label').text(t('supplierEmail'));
    $('#progress-label').text(t('progress'));
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
                shortageList.html('<div style="color:var(--text-muted); font-size:12px; padding:8px;">هیچ کسری وجود ندارد ✅</div>');
            } else {
                notifs.shortage.forEach(item => {
                    shortageList.append(`
                        <div class="notif-item" onclick="goToNode('${item.id}')">
                            <strong>${item.name}</strong><br>
                            <span style="color:#d32f2f;">کسری: ${item.shortage} عدد</span>
                            <span style="color:var(--text-muted);"> (موجود: ${item.available} / نیاز: ${item.required})</span>
                        </div>
                    `);
                });
            }

            const progressList = $('#progress-list');
            progressList.empty();
            if (notifs.in_progress.length === 0) {
                progressList.html('<div style="color:var(--text-muted); font-size:12px; padding:8px;">هیچ موردی در حال ساخت نیست</div>');
            } else {
                notifs.in_progress.forEach(item => {
                    progressList.append(`
                        <div class="notif-item" style="border-right-color:#FF9800;" onclick="goToNode('${item.id}')">
                            <strong>${item.name}</strong><br>
                            <span style="color:var(--text-secondary);">${item.stages} مرحله تعریف شده</span>
                        </div>
                    `);
                });
            }

            const orderList = $('#order-list');
            orderList.empty();
            if (notifs.orders_pending.length === 0) {
                orderList.html('<div style="color:var(--text-muted); font-size:12px; padding:8px;">سفارشی ثبت نشده است</div>');
            } else {
                notifs.orders_pending.forEach(item => {
                    orderList.append(`
                        <div class="notif-item" style="border-right-color:#3498db;" onclick="goToNode('${item.id}')">
                            <strong>${item.name}</strong><br>
                            <span style="color:var(--text-secondary);">${item.count} عدد سفارش</span>
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

    let imgHtml = '<span style="color:var(--text-muted);">بدون عکس</span>';
    if (node.images && node.images.length > 0) {
        const url = node.images[0].url.startsWith('/') ? node.images[0].url : '/' + node.images[0].url;
        imgHtml = `<img src="${url}">`;
    }

    $('#hover-card-img').html(imgHtml);
    $('#hover-card-name').text(node.name);
    $('#hover-card-code').text(`کد فنی: ${node.partCode || '-'}`);

    let stockText = '';
    let statusText = '';
    let statusColor = '';

    if (node.type === 'part') {
        const orderCount = getAncestorOrderCount(nodeId);
        const totalReq = (node.required_quantity || 1) * orderCount;
        const available = node.quantity || 0;
        stockText = `موجودی: ${available} / نیاز کل: ${totalReq}`;

        if (available >= totalReq) {
            statusText = ' موجودی کافی';
            statusColor = '#4CAF50';
        } else if (available > 0) {
            statusText = ' موجودی ناقص';
            statusColor = '#FF9800';
        } else {
            statusText = '🔴 کسری انبار';
            statusColor = '#F44336';
        }
    } else {
        stockText = `نوع: ${node.type === 'product' ? 'محصول' : 'زیرمجموعه'}`;
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
        if (node.order_count > 0) text += ` (${node.order_count} سفارش)`;
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
        'not_started': { title: '🔴 شروع نشده / کسری', cards: [] },
        'in_progress': { title: '🟡 در حال ساخت / ناقص', cards: [] },
        'completed': { title: '🟢 ساخته شده / کافی', cards: [] }
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
                    <div class="kanban-card-info">کد: ${card.code}</div>
                    <div class="kanban-card-info">موجودی: ${card.available} / ${card.required}</div>
                    <div class="kanban-card-info">${card.stages} مرحله</div>
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
        $('#field-partType').val(node.partType || '');

        const required = parseInt(node.required_quantity) || 1;
        const available = parseInt(node.quantity) || 0;
        const orderCount = getAncestorOrderCount(currentNodeId);
        const totalReq = required * orderCount;
        const autoStatus = available >= totalReq ? 'completed' : (available > 0 ? 'in_progress' : 'not_started');
        node.status = autoStatus;

        $(`input[name="status"][value="${autoStatus}"]`).prop('checked', true);

        $('#field-supplier').val(node.supplier || '');
        $('#field-supplier-email').val(node.supplier_email || '');
        toggleSupplierField();

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
        $('#tab-btn-schedule').show();
        $('#tab-btn-docs').hide();
        loadSchedulesForProduct(currentNodeId);
    } else {
        $('#tab-btn-mfg').hide();
        $('#tab-btn-schedule').hide();
        $('#tab-btn-docs').hide();
        $('#progress-container').hide();
        if ($('.tab-btn.active').attr('onclick') === "switchTab('tab-mfg')" || $('.tab-btn.active').attr('onclick') === "switchTab('tab-schedule')") {
            switchTab('tab-general');
        }
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
    $('#progress-completed').text(`${completed} تکمیل شده`);
    $('#progress-remaining').text(`${total - completed} باقی‌مانده`);
}

function toggleSupplierField() {
    const partType = $('#field-partType').val();
    $('#supplier-group').toggle(partType === 'buy');
}

function renderImageGallery(images) {
    const gallery = $('#image-gallery');
    gallery.empty();
    images.forEach((img, index) => {
        const url = img.url.startsWith('/') ? img.url : '/' + img.url;
        const item = $(`
            <div class="gallery-item">
                <img src="${url}" onclick="openModal('${url}')" title="برای بزرگنمایی کلیک کنید">
                <div class="img-label">${img.label || 'تصویر'}</div>
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
        showPromptModal('برچسب عکس', 'برچسب:', 'تصویر', function(label) {
            if (label === null || label === undefined) { currentInput.value = ''; return; }
            const formData = new FormData();
            formData.append('file', file);
            fetch('/api/upload', { method: 'POST', body: formData })
                .then(res => res.json())
                .then(data => {
                    const node = currentData.nodes[currentNodeId];
                    if (!node.images) node.images = [];
                    node.images.push({ url: data.url, label: label || 'تصویر' });
                    renderImageGallery(node.images);
                    currentInput.value = '';
                    autoSaveNode();
                });
        });
    }
}

function removeImage(index) {
    showConfirmModal('آیا از حذف این عکس مطمئن هستید؟', function(result) {
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
        textSpan.html(` شما <strong>${shortage}</strong> عدد کم دارید! (نیاز کل: ${required}، موجود: ${available})`);
        textSpan.css('color', '#d32f2f');
    } else if (shortage === 0) {
        infoDiv.show(); infoDiv.css('background', '#e8f5e9');
        textSpan.html('🟢 موجودی دقیقاً کافی است');
        textSpan.css('color', '#2e7d32');
    } else {
        infoDiv.show(); infoDiv.css('background', '#e3f2fd');
        textSpan.html(` مازاد موجودی: <strong>${Math.abs(shortage)}</strong> عدد`);
        textSpan.css('color', '#1976d2');
    }
}

function renderStages() {
    const list = $('#stages-list');
    list.empty();
    if (tempStages.length === 0) {
        list.html('<p style="color:var(--text-muted); margin:5px; font-size:13px;">هنوز مرحله‌ای تعریف نشده</p>');
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
        const isExpanded = expandedStages[idx] || false;
        const stageKey = stage.id ? `s_${stage.id}` : `idx_${idx}`;

        const item = $(`
            <div class="stage-item-new" data-index="${idx}">
                <span class="stage-drag-handle" style="cursor: grab; color:var(--text-muted);" draggable="true">☰</span>
                <div style="flex:1;min-width:0;">
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        <span class="stage-expand-btn" onclick="event.stopPropagation();toggleStageExpand(${idx})" style="cursor:pointer;font-size:12px;color:var(--accent-blue);user-select:none;">${isExpanded ? '▼' : '▶'}</span>
                        <span class="stage-name">${stage.name}</span>
                        <div class="stage-status-btns">
                            <button class="stage-status-btn ${status === 'not_started' ? 'active-not-started' : ''}" onclick="event.stopPropagation();setStageStatus(${idx}, 'not_started')" title="${currentLang === 'fa' ? 'شروع نشده' : 'Not Started'}">🔴</button>
                            <button class="stage-status-btn ${status === 'in_progress' ? 'active-in-progress' : ''}" onclick="event.stopPropagation();setStageStatus(${idx}, 'in_progress')" title="${currentLang === 'fa' ? 'جاری شده' : 'In Progress'}">🟡</button>
                            <button class="stage-status-btn ${status === 'completed' ? 'active-completed' : ''}" onclick="event.stopPropagation();setStageStatus(${idx}, 'completed')" title="${currentLang === 'fa' ? 'ساخته شده' : 'Completed'}">🟢</button>
                        </div>
                    </div>
                    <div style="display:flex;gap:6px;margin-top:4px;font-size:11px;color:var(--text-muted);flex-wrap:wrap;">
                        <span title="${currentLang === 'fa' ? 'هزینه مواد برآوردی' : 'Est. Material Cost'}">💰 ${t('material')}: <input type="number" step="1000" value="${matCost}" onchange="event.stopPropagation();tempStages[${idx}].estimated_material_cost=Number(this.value);updateCostSummary();autoSaveNode()" style="width:60px;padding:2px 4px;font-size:11px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);"></span>
                        <span title="${currentLang === 'fa' ? 'دستمزد برآوردی' : 'Est. Labor Cost'}">🔧 ${t('labor')}: <input type="number" step="1000" value="${laborCost}" onchange="event.stopPropagation();tempStages[${idx}].estimated_labor_cost=Number(this.value);updateCostSummary();autoSaveNode()" style="width:60px;padding:2px 4px;font-size:11px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);"></span>
                        <span title="${currentLang === 'fa' ? 'سربار برآوردی' : 'Est. Overhead'}">📋 ${t('overhead')}: <input type="number" step="1000" value="${overhead}" onchange="event.stopPropagation();tempStages[${idx}].estimated_overhead=Number(this.value);updateCostSummary();autoSaveNode()" style="width:60px;padding:2px 4px;font-size:11px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);"></span>
                        <span title="${currentLang === 'fa' ? 'ساعت برآوردی' : 'Est. Hours'}">⏱ ${t('hours')}: <input type="number" step="0.5" value="${hours}" onchange="event.stopPropagation();tempStages[${idx}].estimated_hours=Number(this.value);updateCostSummary();autoSaveNode()" style="width:50px;padding:2px 4px;font-size:11px;border:1px solid var(--border-color);border-radius:3px;background:var(--bg-secondary);color:var(--text-primary);"></span>
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
                            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                                <strong style="font-size:12px;">🏭 ${t('manufacturers')}</strong>
                                <button onclick="showAddManufacturerToPart()" class="btn-small" style="padding:2px 8px;font-size:11px;">➕ ${t('addManufacturer')}</button>
                            </div>
                            <div id="part-manufacturers-list" class="manufacturers-list">
                                ${renderPartManufacturersList()}
                            </div>
                        </div>
                    </div>
                    ` : ''}
                </div>
                <button class="stage-remove-btn" onclick="removeStage(${idx})">✕</button>
            </div>
        `);
        const handle = item.find('.stage-drag-handle');
        handle.on('dragstart', function(e) { $(this).closest('.stage-item-new').addClass('dragging'); e.originalEvent.dataTransfer.setData('text/plain', idx); });
        handle.on('dragend', function() { $(this).closest('.stage-item-new').removeClass('dragging'); });
        item.on('dragover', function(e) { e.preventDefault(); });
        item.on('drop', function(e) {
            e.preventDefault();
            const fromIdx = parseInt(e.originalEvent.dataTransfer.getData('text/plain'));
            const toIdx = parseInt($(this).data('index'));
            if (fromIdx !== toIdx && !isNaN(fromIdx)) {
                const movedItem = tempStages.splice(fromIdx, 1)[0];
                tempStages.splice(toIdx, 0, movedItem);
                renderStages();
                autoSaveNode();
            }
        });
        list.append(item);

        if (isExpanded) {
            loadStageDetails(idx, stage);
            refreshManufacturersList();
        }
    });
    updateProgressBar();
    updateCostSummary();
}

function toggleStageExpand(idx) {
    expandedStages[idx] = !expandedStages[idx];
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
        container.html('<div style="font-size:11px;color:var(--text-muted);padding:4px;">هنوز جزئیاتی ثبت نشده. دکمه "افزودن جزئیات" را بزنید.</div>');
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
    $('#detail-modal-title').text('افزودن جزئیات تولید');
    $('#detail-desc').val('');
    $('#detail-modal').fadeIn(150);
}

function editStageDetail(idx, di) {
    const details = stageDetailsMap[idx] || [];
    const d = details[di];
    if (!d) return;
    window._detailStageIdx = idx;
    window._detailEditIdx = di;
    $('#detail-modal-title').text('ویرایش جزئیات تولید');
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
    if (!desc) { showAlertModal('متن جزئیات را وارد کنید'); return; }
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
    showConfirmModal('حذف شود؟', function(result) {
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

function loadPartManufacturers(partId) {
    const pid = parseInt(partId.toString().replace(/^[a-z]/, ''));
    if (isNaN(pid)) return;
    fetch(`/api/v2/parts/${pid}/manufacturers`)
        .then(res => res.json())
        .then(res => {
            if (res.success) {
                partManufacturers = res.data;
                refreshManufacturersList();
            }
        }).catch(e => console.error('loadPartManufacturers error:', e));
}

function loadAllManufacturers() {
    fetch('/api/v2/manufacturers')
        .then(res => res.json())
        .then(res => {
            if (res.success) allManufacturers = res.data;
        });
}

function renderPartManufacturersList() {
    if (!partManufacturers || partManufacturers.length === 0) {
        return '<div style="font-size:11px;color:var(--text-muted);padding:4px;">هیچ سازنده‌ای ثبت نشده</div>';
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
            html += `<div style="margin-bottom:2px;">📧 ایمیل: ${escapeHtml(e.email)}</div>`;
        });
    }
    if (m.phones && m.phones.length) {
        m.phones.forEach(p => {
            html += `<div style="margin-bottom:2px;">📞 تلفن: ${escapeHtml(p.phone)}</div>`;
        });
    }
    if (m.socials && m.socials.length) {
        m.socials.forEach(s => {
            html += `<div style="margin-bottom:2px;">🌐 ${escapeHtml(s.platform)}: ${escapeHtml(s.handle)}</div>`;
        });
    }
    if (m.address) {
        html += `<div style="margin-bottom:2px;">📍 آدرس: ${escapeHtml(m.address)}</div>`;
    }
    if (m.notes) {
        html += `<div style="margin-bottom:2px;">📝 یادداشت: ${escapeHtml(m.notes)}</div>`;
    }
    if (!html) html = '<div style="color:var(--text-muted);">اطلاعاتی ثبت نشده</div>';
    return html;
}

function showAddManufacturerToPart() {
    const unused = allManufacturers.filter(m => !partManufacturers.some(pm => pm.id === m.id));
    const listContainer = $('#mfr-select-list');
    listContainer.empty();
    if (unused.length === 0) {
        listContainer.html('<div style="padding:20px;text-align:center;color:var(--text-muted);">همه سازنده‌ها قبلاً اضافه شده‌اند</div>');
    } else {
        unused.forEach((m, i) => {
            const info = [];
            if (m.emails && m.emails.length) info.push(m.emails[0].email);
            if (m.phones && m.phones.length) info.push(m.phones[0].phone);
            listContainer.append(`
                <div class="select-item" onclick="addManufacturerToPart(${m.id});closeMfrSelectModal();">
                    <div class="select-item-name">${escapeHtml(m.name)}</div>
                    <div class="select-item-info">${info.join(' | ')}</div>
                </div>
            `);
        });
    }
    $('#mfr-select-modal').fadeIn(150);
}

function closeMfrSelectModal() {
    $('#mfr-select-modal').fadeOut(150);
}

function showCreateManufacturerForm() {
    $('#mfr-form-title').text('ایجاد سازنده جدید');
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
            <input type="text" class="mfr-social-platform" placeholder="پلتفرم (Telegram, Instagram, ...)" style="width:40%;">
            <input type="text" class="mfr-social-handle" placeholder="آیدی (@username)" style="width:55%;">
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
    if (!name) { showAlertModal('نام سازنده الزامی است'); return; }
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
                addManufacturerToPart(r.data.id);
            } else {
                showAlertModal('خطا در ایجاد سازنده: ' + (r.error || 'نامشخص'));
            }
        }).catch(e => showAlertModal('خطا در ارتباط با سرور: ' + e.message));
    }
}

function addManufacturerToPart(mfrId) {
    const pid = parseInt(currentNodeId.toString().replace(/^[a-z]/, ''));
    if (isNaN(pid)) { showAlertModal('خطا: قطعه شناسه معتبری ندارد'); return; }
    fetch(`/api/v2/parts/${pid}/manufacturers`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ manufacturer_id: mfrId })
    }).then(res => res.json()).then(r => {
        if (r.success) {
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
    showConfirmModal(`حذف "${partManufacturers[mi].name}" از سازندگان این قطعه؟`, function(result) {
        if (!result) return;
        const mfr = partManufacturers[mi];
        const pid = parseInt(currentNodeId.toString().replace(/^[a-z]/, ''));
        if (isNaN(pid)) return;
        fetch(`/api/v2/parts/${pid}/manufacturers/${mfr.id}`, { method: 'DELETE' })
            .then(res => res.json()).then(r => {
                if (r.success) {
                    partManufacturers.splice(mi, 1);
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
                <span>مواد: <strong>${totalMat.toLocaleString()}</strong></span>
                <span>دستمزد: <strong>${totalLabor.toLocaleString()}</strong></span>
                <span>سربار: <strong>${totalOverhead.toLocaleString()}</strong></span>
                <span>ساعت: <strong>${totalHours}</strong></span>
                <span style="color:var(--accent-green);font-weight:bold;">مجموع: ${grandTotal.toLocaleString()}</span>
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
    if (!name) { showAlertModal('لطفاً نام مرحله را وارد یا انتخاب کنید'); return; }
    tempStages.push({ name: name, status: 'not_started', estimated_material_cost: 0, estimated_labor_cost: 0, estimated_overhead: 0, estimated_hours: 0 });
    $('#new-stage-name').val('');
    renderStages();
    autoSaveNode();
}

function removeStage(idx) {
    showConfirmModal('حذف مرحله "' + tempStages[idx].name + '"؟', function(ok) {
        if (!ok) return;
        tempStages.splice(idx, 1);
        renderStages();
        autoSaveNode();
    });
}

// Inline Edit
function openInlineEdit(nodeId, field, currentValue) {
    inlineEditContext = { nodeId, field };
    $('#inline-edit-title').text(field === 'name' ? 'ویرایش نام' : 'ویرایش مقدار');
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
    if (!currentNodeId) { showAlertModal('⚠️ ابتدا باید روی یک گره کلیک کنید'); return; }
    const parentNode = currentData.nodes[currentNodeId];
    if (parentNode.type === 'part') { showAlertModal('⚠️ قطعه نمی‌تواند زیرمجموعه داشته باشد'); return; }
    const typeName = type === 'assembly' ? 'زیرمجموعه' : 'قطعه';
    showPromptModal(`${typeName} جدید`, `نام ${typeName}:`, `${typeName} جدید`, function(name) {
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
    showConfirmModal('⚠️ آیا از حذف مطمئن هستید؟', function(result) {
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
    if (products.length === 0) { showAlertModal('هیچ محصولی تعریف نشده است!'); return; }
    showProductSelectModal('انتخاب محصول برای خروجی Excel', products, function(pid) {
        window.location.href = `/api/export/excel?product_id=${pid}`;
    });
}

function exportSchematic() {
    const products = [];
    Object.values(currentData.nodes).forEach(node => {
        if (node.type === 'product') products.push({ id: node.id, name: node.name });
    });
    if (products.length === 0) { showAlertModal('هیچ محصولی تعریف نشده است!'); return; }
    showProductSelectModal('انتخاب محصول برای شماتیک', products, function(pid) {
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
    if (!email) { showAlertModal('لطفاً ابتدا ایمیل تأمین‌کننده را وارد کنید'); return; }
    showConfirmModal(`ارسال ایمیل هشدار کمبود به ${email}؟`, function(result) {
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
                container.html('<div style="color:var(--text-muted);padding:10px;font-size:13px;">هیچ مدرک فنی بارگذاری نشده است</div>');
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
                        <a href="${doc.url}" target="_blank" class="btn-small" style="text-decoration:none;background:#4CAF50;">⬇ دانلود</a>
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
    showConfirmModal('آیا از حذف این مدرک مطمئن هستید؟', function(result) {
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
                container.html('<div style="color:var(--text-muted);padding:10px;">برنامه‌ای ثبت نشده است</div>');
                return;
            }
            const statusMap = { planned: 'برنامه‌ریزی شده', in_progress: 'در حال اجرا', completed: 'تکمیل شده', cancelled: 'لغو شده' };
            schedules.forEach(s => {
                container.append(`
                    <div style="background:var(--bg-tertiary);padding:10px;border-radius:6px;margin-bottom:8px;border-right:3px solid ${s.status === 'completed' ? '#4CAF50' : s.status === 'in_progress' ? '#FF9800' : '#2196F3'};">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <strong>${s.quantity} عدد</strong>
                            <span style="font-size:12px;padding:2px 8px;border-radius:10px;background:${s.status === 'completed' ? '#C8E6C9' : s.status === 'in_progress' ? '#FFE0B2' : '#BBDEFB'};">${statusMap[s.status] || s.status}</span>
                        </div>
                        <div style="font-size:12px;color:var(--text-muted);margin-top:5px;">
                            اولویت: ${s.priority} | شروع: ${s.start_date ? new Date(s.start_date).toLocaleDateString('fa-IR') : '-'} | پایان: ${s.end_date ? new Date(s.end_date).toLocaleDateString('fa-IR') : '-'}
                        </div>
                        ${s.notes ? '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;">' + s.notes + '</div>' : ''}
                    </div>
                `);
            });
        });
}

function showAddSchedule() {
    const node = currentData.nodes[currentNodeId];
    if (!node || node.type !== 'product') { showAlertModal('ابتدا یک محصول را انتخاب کنید'); return; }
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
        list.html('<div style="padding:20px;text-align:center;color:var(--text-muted);">هیچ محصولی تعریف نشده</div>');
    } else {
        products.forEach((p, i) => {
            list.append(`
                <div class="select-item" data-pid="${p.id}">
                    <div class="select-item-name">${escapeHtml(p.name)}</div>
                    <div class="select-item-info">${p.order_count ? p.order_count + ' سفارش' : ''}</div>
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
    if (!node || node.type !== 'product') { showAlertModal('ابتدا یک محصول را انتخاب کنید'); return; }

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
        showToast('برنامه تولید با موفقیت ثبت شد');
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