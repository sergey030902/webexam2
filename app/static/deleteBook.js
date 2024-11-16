let deleteBookModal = document.querySelector('#deleteBook');

deleteBookModal.addEventListener('show.bs.modal', function(event){
    let form = document.querySelector('.modal-form');
    form.action = event.relatedTarget.dataset.action;
    let book = deleteBookModal.querySelector('.book-title');
    book.textContent = event.relatedTarget.closest('tr').querySelector('.book_title').textContent;
});
