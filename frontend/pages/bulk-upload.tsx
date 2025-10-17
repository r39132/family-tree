import { useRouter } from 'next/router';
import { useState, useRef } from 'react';
import TopNav from '../components/TopNav';
import { api } from '../lib/api';
import LoadingOverlay from '../components/LoadingOverlay';

interface UploadResponse {
  success: boolean;
  total_in_file: number;
  uploaded_count: number;
  already_present_count: number;
  errors: string[];
  message?: string;
}

export default function BulkUploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [uploadResult, setUploadResult] = useState<UploadResponse | null>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type
      if (!file.name.endsWith('.json')) {
        setValidationErrors(['Please select a JSON file (.json extension)']);
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setValidationErrors([]);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setValidationErrors(['Please select a file first']);
      return;
    }

    setUploading(true);
    setValidationErrors([]);
    setUploadResult(null);

    try {
      // Read file content
      const fileContent = await selectedFile.text();
      
      // Parse JSON
      let jsonData;
      try {
        jsonData = JSON.parse(fileContent);
      } catch (e) {
        setValidationErrors(['Invalid JSON format. Please check your file.']);
        setUploading(false);
        return;
      }

      // Validate basic structure
      if (!jsonData.space_name) {
        setValidationErrors(['Missing required field: space_name']);
        setUploading(false);
        return;
      }

      if (!jsonData.members || !Array.isArray(jsonData.members)) {
        setValidationErrors(['Missing or invalid "members" array']);
        setUploading(false);
        return;
      }

      // Extract space name from filename and compare
      const fileNameParts = selectedFile.name.replace('.json', '').toLowerCase();
      const spaceNameInFile = jsonData.space_name.toLowerCase();
      
      if (!fileNameParts.includes(spaceNameInFile)) {
        setValidationErrors([
          `File name mismatch: The file name "${selectedFile.name}" should contain the family space name "${jsonData.space_name}".`
        ]);
        setUploading(false);
        return;
      }

      // Send to API
      const result = await api('/tree/bulk-upload', {
        method: 'POST',
        body: JSON.stringify(jsonData),
      });

      setUploadResult(result);
      
      if (result.success && result.uploaded_count > 0) {
        // Clear the file input after successful upload
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
        setSelectedFile(null);
      }

    } catch (error: any) {
      const errorMsg = error?.message || 'Upload failed';
      
      // Try to extract detailed error message
      if (errorMsg.includes(':')) {
        const parts = errorMsg.split(':');
        setValidationErrors([parts.slice(1).join(':').trim()]);
      } else {
        setValidationErrors([errorMsg]);
      }
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setValidationErrors([]);
    setUploadResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="container">
      <TopNav showAdd={false} />
      
      <div className="card">
        <h2>Bulk Upload Members</h2>
        <p style={{ marginBottom: '16px', color: '#666' }}>
          Upload multiple family members from a JSON file. The file should follow the required format
          and the filename must contain the family space name (e.g., "demo.json" for the Demo space).
        </p>

        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
            Select JSON File
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileSelect}
            style={{
              display: 'block',
              padding: '8px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              width: '100%',
              maxWidth: '400px',
            }}
          />
          {selectedFile && (
            <p style={{ marginTop: '8px', color: '#666', fontSize: '14px' }}>
              Selected: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(2)} KB)
            </p>
          )}
        </div>

        {/* Validation Errors */}
        {validationErrors.length > 0 && (
          <div
            style={{
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              padding: '12px',
              borderRadius: '4px',
              marginBottom: '20px',
            }}
          >
            <h3 style={{ margin: '0 0 8px 0', color: '#c00' }}>Validation Errors</h3>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              {validationErrors.map((error, idx) => (
                <li key={idx} style={{ color: '#c00' }}>
                  {error}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Upload Result */}
        {uploadResult && (
          <div
            style={{
              backgroundColor: uploadResult.success ? '#efe' : '#fee',
              border: `1px solid ${uploadResult.success ? '#cfc' : '#fcc'}`,
              padding: '12px',
              borderRadius: '4px',
              marginBottom: '20px',
            }}
          >
            <h3
              style={{
                margin: '0 0 12px 0',
                color: uploadResult.success ? '#060' : '#c00',
              }}
            >
              {uploadResult.success ? 'Upload Complete' : 'Upload Completed with Errors'}
            </h3>

            {uploadResult.message && (
              <p style={{ marginBottom: '12px', fontWeight: 'bold' }}>
                {uploadResult.message}
              </p>
            )}

            <div style={{ marginBottom: '12px' }}>
              <p style={{ margin: '4px 0' }}>
                <strong>Total members in file:</strong> {uploadResult.total_in_file}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>Successfully uploaded:</strong> {uploadResult.uploaded_count}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>Already present:</strong> {uploadResult.already_present_count}
              </p>
            </div>

            {uploadResult.errors && uploadResult.errors.length > 0 && (
              <div>
                <h4 style={{ margin: '8px 0', color: '#c00' }}>Errors:</h4>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  {uploadResult.errors.map((error, idx) => (
                    <li key={idx} style={{ color: '#c00', fontSize: '14px' }}>
                      {error}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        <div className="bottombar">
          <div className="bottombar-left">
            <button
              className="btn secondary"
              onClick={() => router.push('/')}
              disabled={uploading}
            >
              Back to Tree
            </button>
          </div>
          <div className="bottombar-right" style={{ display: 'flex', gap: '8px' }}>
            {(selectedFile || uploadResult) && (
              <button
                className="btn secondary"
                onClick={handleReset}
                disabled={uploading}
              >
                Reset
              </button>
            )}
            <button
              className="btn"
              onClick={handleUpload}
              disabled={!selectedFile || uploading}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </div>

        {/* Format Guide */}
        <div
          style={{
            marginTop: '24px',
            padding: '16px',
            backgroundColor: '#f9f9f9',
            borderRadius: '4px',
            border: '1px solid #ddd',
          }}
        >
          <h3 style={{ marginTop: 0 }}>JSON Format Guide</h3>
          <p>Your JSON file should follow this structure:</p>
          <pre
            style={{
              backgroundColor: '#fff',
              padding: '12px',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '13px',
            }}
          >
{`{
  "space_name": "Demo",
  "members": [
    {
      "first_name": "John",
      "last_name": "Doe",
      "dob": "01/15/1980",
      "nick_name": "Johnny",
      "middle_name": "Michael",
      "birth_location": "New York",
      "residence_location": "California",
      "email": "john@example.com",
      "phone": "555-1234",
      "hobbies": ["Reading", "Hiking"],
      "parent_name": "Jane Doe",
      "spouse_name": "Mary Doe"
    }
  ]
}`}
          </pre>
          <p style={{ marginBottom: 0, fontSize: '14px', color: '#666' }}>
            <strong>Required fields:</strong> first_name, last_name, dob (in MM/DD/YYYY format)
            <br />
            <strong>Optional fields:</strong> All other fields including parent_name and spouse_name
            for relationships
          </p>
        </div>
      </div>

      <LoadingOverlay
        isLoading={uploading}
        message="Uploading members..."
        transparent={true}
      />
    </div>
  );
}
