import React from "react";
import { FaHeart, FaTrash, FaEdit } from "react-icons/fa";

const ProductItem = React.memo(({ product, toggleFavorite, deleteProduct, navigate }) => (
  <div className="col-md-4">
    <div className="card shadow-lg border-0 mb-4 rounded-lg">
      <div className="card-body text-center">
        <img
          src={`http://localhost:8000${product.image_url}`}
          alt={product.name}
          className="img-fluid mb-3 rounded"
          style={{ maxHeight: "150px", objectFit: "cover" }}
          loading="lazy"
        />
        <h5 className="card-title fw-bold">{product.name}</h5>
        <p className="card-text text-muted">{product.category}</p>
        <p className="card-text text-primary fw-bold">💰 ${product.price}</p>
        <div className="d-flex justify-content-center gap-3 mt-2">
          <FaHeart
            className={`heart-icon ${product.is_favorite ? "text-danger" : "text-secondary"}`}
            onClick={() => toggleFavorite(product)}
            style={{ cursor: "pointer", fontSize: "20px" }}
          />
          <FaEdit className="text-success" onClick={() => navigate(`/edit-product/${product.id}`)} style={{ cursor: "pointer", fontSize: "20px" }} />
          <FaTrash className="text-danger" onClick={() => deleteProduct(product.id)} style={{ cursor: "pointer", fontSize: "20px" }} />
        </div>
      </div>
    </div>
  </div>
));

export default ProductItem;
