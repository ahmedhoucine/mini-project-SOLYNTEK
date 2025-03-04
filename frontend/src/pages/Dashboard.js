import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import Filters from "../components/Filters";
import ProductList from "../components/ProductList";
import Pagination from "../components/Pagination";

function Dashboard() {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");
  const [currentPage, setCurrentPage] = useState(1);
  const [showFavorites, setShowFavorites] = useState(false);
  const productsPerPage = 6;
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProducts = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        setError("Unauthorized! Please log in.");
        return;
      }
      try {
        const response = await fetch("http://localhost:8000/products", {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
        if (!response.ok) throw new Error("Failed to fetch products");
        const data = await response.json();
        setProducts(data);
      } catch (err) {
        setError(err.message);
      }
    };
    fetchProducts();
  }, []);

  useEffect(() => {
    let filtered = [...products];

    if (searchTerm) {
      filtered = filtered.filter((product) =>
        product.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    if (categoryFilter) {
      filtered = filtered.filter((product) => product.category === categoryFilter);
    }
    if (showFavorites) {
      filtered = filtered.filter((product) => product.is_favorite);
    }

    filtered.sort((a, b) => (sortOrder === "asc" ? a.price - b.price : b.price - a.price));

    setFilteredProducts(filtered);
    setCurrentPage(1);
  }, [searchTerm, categoryFilter, sortOrder, products, showFavorites]);

  const totalPages = useMemo(() => Math.ceil(filteredProducts.length / productsPerPage), [filteredProducts]);
  const paginatedProducts = useMemo(
    () => filteredProducts.slice((currentPage - 1) * productsPerPage, currentPage * productsPerPage),
    [filteredProducts, currentPage]
  );

  return (
    <div className="container mt-5">
      <h2 className="text-center mb-4 text-primary fw-bold">🛒 Product Dashboard</h2>
      {error && <p className="alert alert-danger text-center">{error}</p>}

      <Filters 
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        categoryFilter={categoryFilter}
        setCategoryFilter={setCategoryFilter}
        sortOrder={sortOrder}
        setSortOrder={setSortOrder}
        products={products}
      />

      <div className="d-flex justify-content-center mb-4">
        <button className="btn btn-outline-primary" onClick={() => setShowFavorites((prev) => !prev)}>
          {showFavorites ? "Show All Products" : "Show Favorites Only"}
        </button>
      </div>

      <ProductList products={paginatedProducts} navigate={navigate} setProducts={setProducts} />

      <Pagination totalPages={totalPages} currentPage={currentPage} setCurrentPage={setCurrentPage} />
    </div>
  );
}

export default Dashboard;
