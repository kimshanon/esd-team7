"use client"

import { useState, useRef } from "react"

function RefundRequestComponent({ orderId, onCancel, onSubmit }) {
  const [reason, setReason] = useState("")
  const [details, setDetails] = useState("")
  const [selectedFiles, setSelectedFiles] = useState([])
  const [previews, setPreviews] = useState([])
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files)
      setSelectedFiles(files)

      // Create previews
      const newPreviews = []

      files.forEach((file) => {
        if (file.type.startsWith("image/")) {
          const reader = new FileReader()
          reader.onload = (e) => {
            if (e.target?.result) {
              newPreviews.push(e.target.result)
              setPreviews([...newPreviews])
            }
          }
          reader.readAsDataURL(file)
        }
      })
    }
  }

  const handleRemoveImage = (index) => {
    const newPreviews = [...previews]
    newPreviews.splice(index, 1)
    setPreviews(newPreviews)

    const newFiles = [...selectedFiles]
    newFiles.splice(index, 1)
    setSelectedFiles(newFiles)
  }

  const handleSubmit = () => {
    if (reason) {
      // In a real app, you would send the form data to the server here
      onSubmit()
    }
  }

  return (
    <div className="form-container">
      <div className="form-group">
        <label htmlFor={`refund-reason-${orderId}`}>Reason for Refund</label>
        <select id={`refund-reason-${orderId}`} value={reason} onChange={(e) => setReason(e.target.value)}>
          <option value="">Select a reason</option>
          <option value="missing-items">Missing items</option>
          <option value="wrong-items">Wrong items delivered</option>
          <option value="quality">Poor food quality</option>
          <option value="late">Extremely late delivery</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor={`refund-details-${orderId}`}>Additional Details</label>
        <textarea
          id={`refund-details-${orderId}`}
          placeholder="Please provide more details about your refund request"
          value={details}
          onChange={(e) => setDetails(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Upload Photos (Optional)</label>
        <div className="file-upload">
          <label className="file-upload-button" htmlFor={`refund-photos-${orderId}`}>
            Choose Photos
          </label>
          <input
            type="file"
            id={`refund-photos-${orderId}`}
            accept="image/*"
            multiple
            ref={fileInputRef}
            onChange={handleFileChange}
          />
          <div className="file-name">
            {selectedFiles.length > 0 ? `${selectedFiles.length} file(s) selected` : "No files selected"}
          </div>

          {previews.length > 0 && (
            <div className="image-preview">
              {previews.map((preview, index) => (
                <div key={index} className="preview-container">
                  <img src={preview || "/placeholder.svg"} alt={`Preview ${index}`} />
                  <div className="remove-image" onClick={() => handleRemoveImage(index)}>
                    ×
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="form-buttons">
        <button className="form-button form-button-cancel" onClick={onCancel}>
          Cancel
        </button>
        <button className="form-button form-button-submit" onClick={handleSubmit} disabled={!reason}>
          Submit Request
        </button>
      </div>
    </div>
  )
}

export default RefundRequestComponent

