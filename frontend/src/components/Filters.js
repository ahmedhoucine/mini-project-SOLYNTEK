import React from "react";

function Filters({ searchTerm, setSearchTerm, categoryFilter, setCategoryFilter, sortOrder, setSortOrder, products }) {
  return (
    <div className="d-flex justify-content-between align-items-center mb-4">
      <input
        type="text"
        placeholder="🔍 Search products..."
        className="form-control w-50 shadow-sm"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />
      <select className="form-select w-25 shadow-sm" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
        <option value="">All Categories</option>
        {[...new Set(products.map((p) => p.category))].map((category) => (
          <option key={category} value={category}>{category}</option>
        ))}
      </select>
      <select className="form-select w-25 shadow-sm" value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
        <option value="asc">Sort: Low to High</option>
        <option value="desc">Sort: High to Low</option>
      </select>
    </div>
  );
}

export default Filters;
