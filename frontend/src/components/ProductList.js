import React from "react";
import ProductItem from "./ProductItem";

function ProductList({ products, navigate, setProducts }) {
  const toggleFavorite = async (product) => {
    setProducts((prevProducts) =>
      prevProducts.map((p) => (p.id === product.id ? { ...p, is_favorite: !p.is_favorite } : p))
    );
  };

  const deleteProduct = async (id) => {
    setProducts((prevProducts) => prevProducts.filter((p) => p.id !== id));
  };

  return (
    <div className="row">
      {products.length > 0 ? (
        products.map((product) => (
          <ProductItem key={product.id} product={product} toggleFavorite={toggleFavorite} deleteProduct={deleteProduct} navigate={navigate} />
        ))
      ) : (
        <p className="text-center fw-bold text-muted">No products found.</p>
      )}
    </div>
  );
}

export default ProductList;
