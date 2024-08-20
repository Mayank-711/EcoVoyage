function showSlide(index) {
    slides[currentSlide].classList.remove('visible');
    dots[currentSlide].classList.remove('active');
    currentSlide = index;
    slides[currentSlide].classList.add('visible');
    dots[currentSlide].classList.add('active');
}

function nextSlide() {
    showSlide((currentSlide + 1) % slides.length);
}

function prevSlide() {
    showSlide((currentSlide - 1 + slides.length) % slides.length);
}

setInterval(nextSlide, 10000);