from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CommentForm, NewsletterForm
from .models import Article, Category, Like, Tag


def home(request):
    featured = Article.objects.filter(status='published', is_featured=True).select_related('category', 'author')[:3]
    latest = Article.objects.filter(status='published').select_related('category', 'author')[:12]
    trends = Article.objects.filter(status='published').annotate(likes_total=Count('likes')).order_by('-views_count', '-likes_total')[:5]
    categories = Category.objects.annotate(total=Count('articles')).order_by('-total')
    newsletter_form = NewsletterForm()

    context = {
        'featured': featured,
        'latest': latest,
        'trends': trends,
        'categories': categories,
        'newsletter_form': newsletter_form,
    }
    return render(request, 'news/home.html', context)


def article_list(request):
    query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', '').strip()
    tag_slug = request.GET.get('tag', '').strip()

    articles = Article.objects.filter(status='published').select_related('category', 'author').prefetch_related('tags')

    if query:
        articles = articles.filter(Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query))
    if category_slug:
        articles = articles.filter(category__slug=category_slug)
    if tag_slug:
        articles = articles.filter(tags__slug=tag_slug)

    context = {
        'articles': articles.distinct(),
        'categories': Category.objects.all(),
        'tags': Tag.objects.all()[:25],
        'query': query,
        'selected_category': category_slug,
        'selected_tag': tag_slug,
    }
    return render(request, 'news/article_list.html', context)


def article_detail(request, slug):
    article = get_object_or_404(
        Article.objects.select_related('category', 'author').prefetch_related('tags', 'comments__user'),
        slug=slug,
        status='published',
    )
    Article.objects.filter(pk=article.pk).update(views_count=F('views_count') + 1)
    article.refresh_from_db(fields=['views_count'])

    comments = article.comments.select_related('user')
    liked = request.user.is_authenticated and Like.objects.filter(article=article, user=request.user).exists()

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.article = article
            comment.user = request.user
            comment.save()
            messages.success(request, 'Комментарий опубликован.')
            return redirect(article.get_absolute_url())
    else:
        comment_form = CommentForm()

    related = Article.objects.filter(status='published', category=article.category).exclude(pk=article.pk)[:4]

    return render(request, 'news/article_detail.html', {
        'article': article,
        'comments': comments,
        'comment_form': comment_form,
        'liked': liked,
        'related': related,
    })


@login_required
@require_POST
def toggle_like(request, slug):
    article = get_object_or_404(Article, slug=slug, status='published')
    like, created = Like.objects.get_or_create(article=article, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({'liked': liked, 'likes_count': article.likes.count()})


@require_POST
def newsletter_subscribe(request):
    form = NewsletterForm(request.POST)
    if form.is_valid():
        messages.success(request, 'Спасибо! Вы подписались на рассылку.')
    else:
        messages.error(request, 'Введите корректный email.')
    return redirect('news:home')
