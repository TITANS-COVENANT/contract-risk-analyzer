"use client";

import { useCallback, useState } from "react";
import { useDropzone, type FileRejection } from "react-dropzone";

interface FileUploadProps {
  disabled?: boolean;
  selectedName?: string | null;
  onFile: (file: File) => void;
}

export default function FileUpload({
  disabled = false,
  selectedName = null,
  onFile,
}: FileUploadProps) {
  const [localError, setLocalError] = useState<string | null>(null);

  const onDrop = useCallback(
    (accepted: File[], rejections: FileRejection[]) => {
      setLocalError(null);

      if (rejections.length > 0) {
        const code = rejections[0]?.errors[0]?.code;
        if (code === "file-too-large") {
          setLocalError("File is too large. Maximum size is 15 MB.");
        } else if (code === "file-invalid-type") {
          setLocalError("Only PDF files are supported.");
        } else {
          setLocalError("That file could not be accepted. Please try a PDF under 15 MB.");
        }
        return;
      }

      if (accepted[0]) {
        onFile(accepted[0]);
      }
    },
    [onFile],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled,
    multiple: false,
    accept: { "application/pdf": [".pdf"] },
    maxSize: 15 * 1024 * 1024,
  });

  return (
    <div>
      <div
        {...getRootProps()}
        className={`dropzone${isDragActive ? " active" : ""}${disabled ? " disabled" : ""}`}
        aria-disabled={disabled}
      >
        <input {...getInputProps()} />
        <div className="dropzone-icon" aria-hidden="true">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 16V4m0 0l-4 4m4-4l4 4M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"
            />
          </svg>
        </div>
        <strong>
          {isDragActive ? "Drop the PDF to analyze" : "Drop a contract PDF here"}
        </strong>
        <p>or click to browse · PDF only · max 15 MB</p>
        <p>
          Text-based English contracts work best. Scanned images need OCR (not
          supported yet).
        </p>
        {selectedName ? (
          <span className="file-pill">
            <span className="file-pill-dot" />
            {selectedName}
          </span>
        ) : null}
      </div>
      {localError ? <div className="error">{localError}</div> : null}
    </div>
  );
}
