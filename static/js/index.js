document.querySelectorAll('#navbar ul li a').forEach(link => {
    link.addEventListener('mouseover', (event) => {
        const targetId = link.getAttribute('href').substring(1); // Get section ID
        const targetSection = document.getElementById(targetId); // Find target section

        if (targetSection) {
            // Smooth scroll to the target section
            targetSection.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

  function startAnalysis() {
    // Show progress bar
    document.getElementById("progressContainer").style.display = "block";
    const progressBar = document.getElementById("progressBar");

    // Create FormData from the form
    const formData = new FormData(document.getElementById("uploadForm"));

    // Send form data with AJAX
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/index", true);

    // Update progress bar based on upload progress
    xhr.upload.onprogress = function (event) {
      if (event.lengthComputable) {
        const percentComplete = (event.loaded / event.total) * 100;
        progressBar.style.width = percentComplete + "%";
      }
    };

    // When the upload is complete, redirect to results page
    xhr.onload = function () {
      if (xhr.status === 200) {
        // Complete the progress bar animation
        progressBar.style.width = "100%";
        // Redirect to the results page after a short delay
        setTimeout(() => {
          window.location.href = "/results";
        }, 500);
      } else {
        alert("Error during analysis. Please try again.");
      }
    };

    // Send the form data
    xhr.send(formData);
  }

  function updateClock() {
    const now = new Date();
    const hours = now.getHours().toString().padStart(2, '0');
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const seconds = now.getSeconds().toString().padStart(2, '0');
    const day = now.getDate().toString().padStart(2, '0');
    const month = (now.getMonth() + 1).toString().padStart(2, '0');
    const year = now.getFullYear();

    const time = `${hours}:${minutes}:${seconds}`;
    const date = `${day}-${month}-${year}`;

    document.getElementById('clock').textContent = time;
    document.getElementById('date').textContent = date;
  }

  setInterval(updateClock, 1000); // Update every second
  updateClock(); // Initial call to set the clock immediately

