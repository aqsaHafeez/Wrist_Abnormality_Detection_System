// Scroll to section on hover
document.querySelectorAll('#navbar ul li a').forEach(link => {
    link.addEventListener('mouseover', (event) => {
      event.preventDefault(); // Prevent default link behavior
      const targetId = link.getAttribute('href').substring(1); // Get section ID
      const targetSection = document.getElementById(targetId); // Find target section
  
      if (targetSection) {
        // Smooth scroll to the target section
        targetSection.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });
  