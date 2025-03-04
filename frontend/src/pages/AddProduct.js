import React, { useState, useCallback } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { useDropzone } from "react-dropzone";

function AddProduct() {
  const [productData, setProductData] = useState({
    name: "",
    description: "",
    price: "",
    category: "",
    is_favorite: false,
    image: null,
  });

  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const onDrop = useCallback((acceptedFiles) => {
    setProductData((prevData) => ({
      ...prevData,
      image: acceptedFiles[0],
    }));
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: "image/*",
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setProductData((prevData) => ({
      ...prevData,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      if (!token) throw new Error("No authentication token found.");

      const formData = new FormData();
      formData.append(
        "product",
        JSON.stringify({
          name: productData.name,
          description: productData.description,
          price: productData.price,
          category: productData.category,
          is_favorite: productData.is_favorite,
        })
      );
      if (productData.image) formData.append("image", productData.image);

      await axios.post("http://localhost:8000/products", formData, {
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "multipart/form-data" },
      });

      navigate("/dashboard");
    } catch (err) {
      setError(err.response ? err.response.data.detail : err.message);
    }
  };

  return (
    <div className="container mt-5">
      <h2>Add Product</h2>
      {error && <div className="alert alert-danger">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label htmlFor="name" className="form-label">Product Name</label>
          <input type="text" className="form-control" id="name" name="name" value={productData.name} onChange={handleChange} required />
        </div>

        <div className="mb-3">
          <label htmlFor="description" className="form-label">Description</label>
          <textarea className="form-control" id="description" name="description" rows="3" value={productData.description} onChange={handleChange} required></textarea>
        </div>

        <div className="mb-3">
          <label htmlFor="price" className="form-label">Price</label>
          <input type="number" className="form-control" id="price" name="price" value={productData.price} onChange={handleChange} required />
        </div>

        <div className="mb-3">
          <label htmlFor="category" className="form-label">Category</label>
          <input type="text" className="form-control" id="category" name="category" value={productData.category} onChange={handleChange} required />
        </div>

        <div className="mb-3">
          <label className="form-label">Upload Image</label>
          <div {...getRootProps()} className="border p-4 text-center border-dashed cursor-pointer">
            <input {...getInputProps()} />
            {isDragActive ? <p>Drop the image here...</p> : <p>Drag & drop an image, or click to select</p>}
          </div>
          {productData.image && <img src={URL.createObjectURL(productData.image)} alt="Preview" width={100} className="mt-2" />}
        </div>

        <div className="mb-3 form-check">
          <input type="checkbox" className="form-check-input" id="is_favorite" name="is_favorite" checked={productData.is_favorite} onChange={handleChange} />
          <label className="form-check-label" htmlFor="is_favorite">Is Favorite</label>
        </div>

        <button type="submit" className="btn btn-primary">Add Product</button>
      </form>
    </div>
  );
}

export default AddProduct;
