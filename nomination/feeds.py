from django.core.urlresolvers import reverse
from django.contrib.syndication.views import Feed, FeedDoesNotExist
from nomination.views import get_project
from django.utils.feedgenerator import Atom1Feed

class url_feed(Feed):

    Atom1Feed.mime_type = 'application/xml'
    feed_type = Atom1Feed

    def get_object(self, request, slug):
        self.slug = slug
        self.project = get_project(self.slug)
        self.site_names = dict(self.project.url_set.filter(attribute__iexact='Site_Name').order_by('-date').values_list('entity', 'value'))
        self.url_titles = dict(self.project.url_set.filter(attribute__iexact='Title').order_by('-date').values_list('entity', 'value'))
        self.descriptions = dict(self.project.url_set.filter(attribute__iexact='Description').order_by('-date').values_list('entity', 'value'))

        return  self.project

    def title(self, obj):
        """Returns the title for the feed."""
        return "Latest URLs for " + obj.project_name

    def link(self, obj):
        """Returns the link for the feed."""
        if not obj:
            raise FeedDoesNotExist
        return reverse('url_feed', args=[self.slug])

    def subtitle(self, obj):
        """Returns the subtitle for the feed."""
        return "RSS feed for the most recent URLs added to " + \
            obj.project_name + "."

    def items(self, obj):
        """Returns the items for the feed."""
        return obj.url_set.all().filter(attribute__iexact='surt').order_by('-date')

    def item_link(self, item):
        """Takes an item from items(), and returns its URL."""
        return reverse('url_listing', args=[self.slug, item.entity])

    def item_pubdate(self, item):
        """Takes an item from items(), and returns its added date."""
        return item.date

    def item_title(self, item):
        """Takes an item from items(), and returns its title."""
        # return url if there is no title
        title = item.entity
        try:
            title = self.site_names[item.entity]
        except:
            try:
                title = self.url_titles[item.entity]
            except:
                pass
        return title

    def item_description(self, item):
        try:
            return "%s - %s" % (item.entity, self.descriptions[item.entity])
        except:
            return item.entity


class nomination_feed(Feed):

    Atom1Feed.mime_type = 'application/xml'
    feed_type = Atom1Feed

    def get_object(self, request, slug):
        self.slug = slug
        self.project = get_project(self.slug)
        return  self.project

    def title(self, obj):
        """Returns the title for the feed."""
        return "Most Recent Nominations for " + obj.project_name

    def link(self, obj):
        """Returns the link for the feed."""
        if not obj:
            raise FeedDoesNotExist
        return reverse('nomination_feed', args=[self.slug,])

    def subtitle(self, obj):
        """Returns the subtitle for the feed."""
        return "RSS feed for the most recently nominated URLs for " + \
            obj.project_name + ". Includes newly added URLs " + \
            "and subsequent nominations of those URLs."

    def items(self, obj):
        """Returns the items for the feed."""
        return obj.url_set.all().filter(attribute__iexact='nomination').order_by('-date')

    def item_link(self, item):
        """Takes an item from items(), and returns its URL."""
        return reverse('url_listing', args=[self.slug, item.entity])

    def item_pubdate(self, item):
        """Takes an item from items(), and returns its nomination date."""
        return item.date

    def item_title(self, item):
        """Takes an item from items(), and returns its title."""
        # return url if there is no title
        title = item.entity
        try:
            title = self.project.url_set.get(entity__exact=item.entity, attribute="Site_Name").value
        except:
            try:
                title = self.project.url_set.get(entity__exact=item.entity, attribute="Title").value
            except:
                pass
        return title

    def item_description(self, item):
        try:
            return "%s - %s" % (item.entity, self.project.url_set.get(entity__exact=item.entity, attribute="Description").value)
        except:
            return item.entity
