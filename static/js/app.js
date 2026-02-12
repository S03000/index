function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i += 1) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === `${name}=`) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

const likeBtn = document.querySelector('[data-like-btn]');
if (likeBtn) {
  likeBtn.addEventListener('click', async () => {
    const slug = likeBtn.dataset.slug;
    const response = await fetch(`/articles/${slug}/like/`, {
      method: 'POST',
      headers: { 'X-CSRFToken': getCookie('csrftoken') },
    });
    if (response.ok) {
      const payload = await response.json();
      likeBtn.classList.toggle('liked', payload.liked);
      likeBtn.querySelector('span').textContent = payload.likes_count;
    }
  });
}
