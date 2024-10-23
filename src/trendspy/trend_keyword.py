from datetime import datetime, timezone
from .news_article import NewsArticle
from .utils import ensure_list, truncate_string

class TrendKeyword:
	"""
	Represents a trending search term with associated metadata.

	This class encapsulates information about a trending keyword, including
	its search volume, related news, geographic information, and timing data.

	Attributes:
		keyword (str): The trending search term
		news (list): Related news articles
		geo (str): Geographic location code
		started_timestamp (tuple): When the trend started
		ended_timestamp (tuple): When the trend ended (if finished)
		volume (int): Search volume
		volume_growth_pct (float): Percentage growth in search volume
		trend_keywords (list): Related keywords
		topics (list): Related topics
		news_tokens (list): Associated news tokens
		normalized_keyword (str): Normalized form of the keyword
	"""
	def __init__(self, item: list):
		(
			self.keyword,
			self.news, # news!
			self.geo,
			self.started_timestamp,
			self.ended_timestamp,
			self._unk2,
			self.volume,
			self._unk3,
			self.volume_growth_pct,
			self.trend_keywords,
			self.topics,
			self.news_tokens,
			self.normalized_keyword
		) = item
		if self.news:
			self.news = list(map(NewsArticle.from_api, self.news))

	def _convert_to_datetime(self, raw_time):
		"""Converts time in seconds to a datetime object with UTC timezone, if it exists."""
		return datetime.fromtimestamp(raw_time, tz=timezone.utc) if raw_time else None

	@property
	def is_trend_finished(self) -> bool:
		"""Checks if the trend is finished."""
		return self.ended_timestamp is not None

	def hours_since_started(self) -> float:
		"""Returns the number of hours elapsed since the trend started."""
		if not self.started_timestamp:
			return 0
		delta = datetime.now(tz=timezone.utc) - datetime.fromtimestamp(self.started_timestamp[0], tz=timezone.utc)
		return delta.total_seconds() / 3600

	def __str__(self):
		timeframe = datetime.fromtimestamp(self.started_timestamp[0]).strftime('%Y-%m-%d %H:%M:%S')
		if self.is_trend_finished:
			timeframe += ' - '+datetime.fromtimestamp(self.ended_timestamp[0]).strftime('%Y-%m-%d %H:%M:%S')
		else:
			timeframe += ' - now'
			
		s =    'Keyword        : {}'.format(self.keyword)
		s += '\nGeo            : {}'.format(self.geo)
		s += '\nVolume         : {} ({}%)'.format(self.volume, self.volume_growth_pct)
		s += '\nTimeframe      : {}'.format(timeframe)
		s += '\nTrend keywords : {} keywords ({})'.format(
			len(self.trend_keywords),
			truncate_string(','.join(self.trend_keywords), 50)
		)
		s += '\nNews tokens    : {} tokens'.format(len(self.news_tokens))
		return s

	def __repr__(self):
		return (
			f"TrendKeyword(keyword='{self.keyword}', geo='{self.geo}', volume={self.volume}, "
			f"started_timestamp={self.started_timestamp}, ended_timestamp={self.ended_timestamp})"
		)

class TrendKeywordLite:
	"""
	A lightweight version of TrendKeyword for simple trend representation.

	This class provides a simplified view of trending keywords, primarily used
	for RSS feeds and basic trending data.

	Attributes:
		keyword (str): The trending search term
		volume (str): Approximate search volume
		trend_keywords (list): Related keywords
		link (str): URL to more information
		started (int): Unix timestamp when the trend started
		picture (str): URL to related image
		picture_source (str): Source of the picture
		news (list): Related news articles
	"""
	def __init__(self, keyword, volume, trend_keywords, link, started, picture, picture_source, news):
		self.keyword = keyword
		self.volume = volume
		self.trend_keywords = trend_keywords
		self.link = link
		self.started = None
		self.picture = picture
		self.picture_source = picture_source
		self.news = news
		if started:
			self.started = self._parse_pub_date(started)
		elif news:
			self.started = min([item.time for item in news])

	@staticmethod
	def _parse_pub_date(pub_date):
		return int(datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %z').timestamp())

	@classmethod
	def from_api(cls, data):
		title = data.get('title')
		if isinstance(title, dict):
			title = title.get('query')
		volume          = data.get('formattedTraffic') or data.get('approx_traffic')
		trend_keywords  = ([item.get('query') for item in data.get('relatedQueries', [])])
		trend_keywords  = trend_keywords or (data.get('description', '').split(', ') if 'description' in data else None)
		trend_keywords  = trend_keywords or list(set([word for item in data.get('idsForDedup', '') for word in item.split(' ')]))
		link            = data.get('shareUrl') or data.get('link')
		started         = data.get('pubDate')
		picture         = data.get('picture') or data.get('image', {}).get('imageUrl')
		picture_source  = data.get('picture_source') or data.get('image', {}).get('source')
		articles        = data.get('articles') or data.get('news_item') or []

		return cls(
			keyword			= title,
			volume			= volume,
			trend_keywords 	= trend_keywords,
			link			= link,
			started         = started,
			picture         = picture,
			picture_source  = picture_source,
			news            = [NewsArticle.from_api(item) for item in ensure_list(articles)]
		)

	def __repr__(self):
		return f"TrendKeywordLite(title={self.keyword}, traffic={self.volume}, started={self.started})"

	def __str__(self):
		s  =   'Keyword        : {}'.format(self.keyword)
		s += '\nVolume         : {}'.format(self.volume) if self.volume else ''
		s += '\nStarted        : {}'.format(datetime.fromtimestamp(self.started).strftime('%Y-%m-%d %H:%M:%S')) if self.started else ''
		s += '\nTrend keywords : {} keywords ({})'.format(len(self.trend_keywords), truncate_string(','.join(self.trend_keywords), 50)) if self.trend_keywords else ''
		s += '\nNews           : {} news'.format(len(self.news)) if self.news else ''
		return s