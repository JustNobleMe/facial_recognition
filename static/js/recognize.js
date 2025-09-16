const video = document.getElementById('video');
const canvas = document.getElementById('overlay');
const ctx = canvas.getContext('2d');
const upload = document.getElementById('upload');
const preview = document.getElementById('upload-preview');

// Access webcam
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => { video.srcObject = stream; })
  .catch(err => console.error("Error accessing webcam:", err));

// Send live frames to Flask every .5s
setInterval(() => {
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob(blob => {
    const formData = new FormData();
    formData.append("frame", blob, "frame.jpg");

    fetch("/recognize_live", { method: "POST", body: formData })
      .then(res => res.json())
      .then(data => {
        if (data.name) {
          // Draw result
          ctx.strokeStyle = "lime";
          ctx.lineWidth = 3;
          ctx.strokeRect(100, 100, 120, 160); // Example box
          ctx.fillStyle = "lime";
          ctx.font = "20px Arial";
          ctx.fillText(data.name, 100, 90);
        }
      });
  }, "image/jpeg");
}, 500);

// Handle file upload
// upload.addEventListener("change", e => {
//   const file = e.target.files[0];
//   if (file) {
//     const reader = new FileReader();
//     reader.onload = event => {
//       preview.src = event.target.result;
//       preview.style.display = "block";
//     };
//     reader.readAsDataURL(file);

//     const formData = new FormData();
//     formData.append("file", file);

//     fetch("/recognize_upload", { method: "POST", body: formData })
//       .then(res => res.json())
//       .then(data => {
//         alert("Recognized: " + (data.name || "Unknown"));
//       });
//   }
// });
