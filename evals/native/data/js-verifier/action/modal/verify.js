// Validation: Check if the second modal is open
//
// Objective: Click "Open first modal" to open the modal dialog.
// Then click "Open second modal" inside the first modal to open the second modal.
//
// Based on observed changes from changes.json:
// 1. attr_modified: DIV#exampleModalToggle2 class changed from "modal fade" to "modal fade show"
// 2. node_added: DIV.modal-backdrop was added to the DOM

// Check 1: The second modal (#exampleModalToggle2) should have class "show"
// This indicates the modal is visible and active
const secondModal = document.querySelector('#exampleModalToggle2');
const hasShowClass = secondModal && secondModal.classList.contains('show');

// Check 2: Modal backdrop should be present (added when modal opens)
// Bootstrap adds this overlay element when a modal is displayed
const modalBackdrop = document.querySelector('.modal-backdrop');

// Both conditions must be true for the second modal to be open
hasShowClass && modalBackdrop !== null