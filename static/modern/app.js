$(document).ready(function() {
    $('body').on('click', '.modal-close, .modal-overlay', function(e) {
        if ($(e.target).hasClass('modal-overlay') || $(e.target).hasClass('modal-close')) {
            $(this).closest('.modal-overlay').hide();
        }
    });
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') $('.modal-overlay').hide();
    });
});
