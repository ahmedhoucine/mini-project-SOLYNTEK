import React from "react";

function Pagination({ totalPages, currentPage, setCurrentPage }) {
  return (
    <div className="d-flex justify-content-center mt-4">
      {Array.from({ length: totalPages }, (_, i) => (
        <button key={i + 1} className={`btn mx-1 rounded-pill ${currentPage === i + 1 ? "btn-primary" : "btn-outline-primary"}`} onClick={() => setCurrentPage(i + 1)}>
          {i + 1}
        </button>
      ))}
    </div>
  );
}

export default Pagination;
    