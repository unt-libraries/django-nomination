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
        # Save these dicts of URLs and attributes in the class so we can save on queries later.
        self.site_names = dict(self.project.url_set.filter(attribute__iexact='Site_Name')
                               .order_by('-date').values_list('entity', 'value'))
        self.url_titles = dict(self.project.url_set.filter(attribute__iexact='Title')
                               .order_by('-date').values_list('entity', 'value'))
        self.descriptions = dict(self.project.url_set.filter(attribute__iexact='Description')
                                 .order_by('-date').values_list('entity', 'value'))

        return self.project

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
        except KeyError:
            try:
                title = self.url_titles[item.entity]
            except KeyError:
                pass
        return title

    def item_description(self, item):
        try:
            return "%s - %s" % (item.entity, self.descriptions[item.entity])
        except KeyError:
            return item.entity


class nomination_feed(Feed):

    Atom1Feed.mime_type = 'application/xml'
    feed_type = Atom1Feed

    def get_object(self, request, slug):
        self.slug = slug
        self.project = get_project(self.slug)

        # Generate URL/attribute value dicts, excluding entities with multiple values
        # for the same attribute (using no_dup_dict). This prevents incorrectly
        # associating attribute values from other nominations of the same entity.
        temp = (
            self.project.url_set.filter(attribute__iexact='Site_Name')
                                .values_list('entity', 'value')
        )
        self.site_names = no_dup_dict(temp)
        temp = (
            self.project.url_set.filter(attribute__iexact='Title')
                                .values_list('entity', 'value')
        )
        self.url_titles = no_dup_dict(temp)
        temp = (
            self.project.url_set.filter(attribute__iexact='Description')
                                .values_list('entity', 'value')
        )
        self.descriptions = no_dup_dict(temp)
        return self.project

    def title(self, obj):
        """Returns the title for the feed."""
        return "Most Recent Nominations for " + obj.project_name

    def link(self, obj):
        """Returns the link for the feed."""
        if not obj:
            raise FeedDoesNotExist
        return reverse('nomination_feed', args=[self.slug])

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
            title = self.site_names[item.entity]
        except KeyError:
            try:
                title = self.url_titles[item.entity]
            except KeyError:
                pass
        return title

    def item_description(self, item):
        try:
            return "%s - %s" % (item.entity, self.descriptions[item.entity])
        except KeyError:
            return item.entity


def no_dup_dict(url_set):
    """Create a dictionary from list of lists.

    This function expects a list of 2-tuples of the form (key, value),
    where key becomes the dictionary key and value becomes the associated
    value. In the event that there are more than 1 2-tuples with the same
    key, no entries are made into the dictionary.
    """
    attr_dict = {}
    del_list = []
    for entity, attribute in url_set:
        if entity in attr_dict:
            del_list.append(entity)
        else:
            attr_dict[entity] = attribute
    # For all the entities that had duplicates, delete the dict entry.
    for entity in set(del_list):
        del(attr_dict[entity])
    return attr_dict
