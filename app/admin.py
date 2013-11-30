import app.basic
import tornado.web
import settings
import datetime

from lib import companiesdb
from lib import hackpad
from lib import postsdb
from lib import userdb

###########################
### ADMIN COMPANY
### /admin/company
###########################
class AdminCompany(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self):
    if self.current_user not in settings.get('staff'):
      self.redirect('/')
    else:
      slug = self.get_argument('slug', '')

      company = {
        'id':'', 'name':'', 'url':'', 'description':'', 'logo_filename':'',
        'locations':'', 'investment_series':'', 'investment_year':'', 'categories':'',
        'satus':'', 'slug':'', 'investment_post_slug':''
      }
      if slug != '':
        company = companiesdb.get_company_by_slug(slug)
        if not company:
          company = {
            'id':'', 'name':'', 'url':'', 'description':'', 'logo_filename':'',
            'locations':'', 'investment_series':'', 'investment_year':'', 'categories':'',
            'satus':'', 'slug':'', 'investment_post_slug':''
          }

      self.render('admin/admin_company.html', company=company)

  @tornado.web.authenticated
  def post(self):
    if self.current_user not in settings.get('staff'):
      self.redirect('/')
    else:
      company = {}
      company['id'] = self.get_argument('id', '')
      company['name'] = self.get_argument('name', '')
      company['url'] = self.get_argument('url', '')
      company['description'] = self.get_argument('description', '')
      company['logo_filename'] = self.get_argument('logo_filename', '')
      company['locations'] = self.get_argument('locations', '')
      company['investment_series'] = self.get_argument('investment_series', '')
      company['investment_year'] = self.get_argument('investment_year', '')
      company['categories'] = self.get_argument('categories', '')
      company['status'] = self.get_argument('status', '')
      company['slug'] = self.get_argument('slug', '')
      company['investment_post_slug'] = self.get_argument('investment_post_slug', '')

      # save the company details
      companiesdb.save_company(company)

      self.render('admin/admin_company.html', company=company)

###########################
### List the available admin tools
### /admin
###########################
class AdminHome(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self):
    if self.current_user not in settings.get('staff'):
      self.redirect('/')
    else:
      self.render('admin/admin_home.html')

###########################
### View system statistics
### /admin/stats
###########################
class AdminStats(app.basic.BaseHandler):
  def get(self):
    if self.current_user not in settings.get('staff'):
      self.redirect('/')
    else:
      total_posts = postsdb.get_post_count()
      total_users = userdb.get_user_count()

    self.render('admin/admin_stats.html', total_posts=total_posts, total_users=total_users)

###########################
### Add a user to the blacklist
### /users/(?P<username>[A-z-+0-9]+)/ban
###########################
class BanUser(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self, screen_name):
    if self.current_user in settings.get('staff'):
      user = userdb.get_user_by_screen_name(screen_name)
      if user:
        user['user']['is_blacklisted'] = True
        userdb.save_user(user)
    self.redirect('/')

###########################
### Move the sort_score for a post up (for hot list)
### /posts/([^\/]+)/bumpup
###########################
class BumpUp(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self, slug):
    post = postsdb.get_post_by_slug(slug)

    if self.current_user_can('super_upvote_posts'):
      post['sort_score'] += 0.25
      postsdb.save_post(post)

    self.redirect('/?sort_by=hot')

###########################
### Move the sort_socre for post down (for hot list)
### /posts/([^\/]+)/bumpdown
###########################
class BumpDown(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self, slug):
    post = postsdb.get_post_by_slug(slug)

    if self.current_user_can('downvote_posts'):
      post['sort_score'] -= 0.25
      postsdb.save_post(post)

    self.redirect('/?sort_by=hot')

###########################
### List posts that are marekd as deleted
### /admin/delete_user
###########################
class DeletedPosts(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self):
    if not self.current_user_can('delete_posts'):
      self.redirect('/')
    else:
      page = abs(int(self.get_argument('page', '1')))
      per_page = abs(int(self.get_argument('per_page', '10')))

      deleted_posts = postsdb.get_deleted_posts(per_page, page)
      total_count = postsdb.get_deleted_posts_count()

      self.render('admin/deleted_posts.html', deleted_posts=deleted_posts, total_count=total_count, page=page, per_page=per_page)

###########################
### Mark all shares by a user as 'deleted'
### /admin/deleted_posts
###########################
class DeleteUser(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self):
    if not self.current_user_can('delete_users'):
      self.redirect('/')
    else:
      msg = self.get_argument('msg', '')
      self.render('admin/delete_user.html', msg=msg)

  @tornado.web.authenticated
  def post(self):
    if not self.current_user_can('delete_users'):
      self.redirect('/')
    else:
      msg = self.get_argument('msg', '')
      post_slug = self.get_argument('post_slug', '')
      post = postsdb.get_post_by_slug(post_slug)
      if post:
        # get the author of this post
        screen_name = post['user']['screen_name']
        postsdb.delete_all_posts_by_user(screen_name)
      self.ender('admin/delete_user.html', msg=msg)

###########################
### Create a new hackpad
### /generate_hackpad/?
###########################
class GenerateNewHackpad(app.basic.BaseHandler):
  def get(self):
    if self.current_user not in settings.get('staff'):
      self.redirect('/')
    else:
      hackpads = hackpad.create_hackpad()
      self.api_response(hackpads)

###########################
### List all hackpads
### /list_hackpads
###########################
class ListAllHackpad(app.basic.BaseHandler):
  def get(self):
    if self.current_user not in settings.get('staff'):
      self.redirect('/')
    else:
      hackpads = hackpad.list_all()
      self.api_response(hackpads)

###########################
### Mute (hide) a post
### /posts/([^\/]+)/mute
###########################
class Mute(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self, slug):
    post = postsdb.get_post_by_slug(slug)

    if post and self.current_user_can('mute_posts'):
      post['muted'] = True
      postsdb.save_post(post)

    self.redirect('/?sort_by=hot')

###########################
### Recalc the sort socres (for hot list)
### /admin/sort_posts
###########################
class ReCalculateScores(app.basic.BaseHandler):
  def get(self):
    # set our config values up
    #staff_bonus = int(self.get_argument('staff_bonus', -3))
    staff_bonus = -3
    #time_penalty_multiplier = float(self.get_argument('time_penalty_multiplier', 2.0))
    time_penalty_multiplier = 2.0
    #grace_period = float(self.get_argument('grace_period', 6.0))
    grace_period = 6.0
    #comments_multiplier = float(self.get_argument('comments_multiplier', 3.0))
    comments_multiplier = 3.0
    #bumps_multiplier = float(self.get_argument('bumps_multiplier', 1.0))
    bumps_multiplier = 1.0
    #min_bumps = float(self.get_argument('min_bumps', 2))
    min_bumps = 2

    # get all the posts that have at least the 'min vote threshold'
    posts = postsdb.get_posts_with_min_bumps(min_bumps)

    data = []
    for post in posts:
      # determine how many hours have elapsed since this post was created
      tdelta = datetime.datetime.now() - post['date_created']
      hours_elapsed = tdelta.seconds/3600 + tdelta.days*24

      # determine the penalty for time decay
      time_penalty = 0
      if hours_elapsed > grace_period:
        time_penalty = hours_elapsed - grace_period
      if hours_elapsed > 12:
        time_penalty = time_penalty * 1.5
      if hours_elapsed > 18:
        time_penalty = time_penalty * 2

      # get our base score from downbumps
      base_score = post['downbumps'] * -1

      # determine if we should assign a staff bonus or not
      if post['user']['username'] in settings.get('staff'):
        staff_bonus = staff_bonus
      else:
        staff_bonus = 0

      # determine how to weight bumps
      bumps_base_score = 0
      if post['bumps'] == 1 and post['comment_count'] > 2:
        bumps_base_score = -2
      if post['bumps'] > 8 and post['comment_count'] == 0:
        bumps_base_score = -2

      scores = {}
      # now actually calculate the score
      total_score = base_score
      
      scores['bumps'] = (bumps_base_score + post['bumps'] * bumps_multiplier)
      total_score += scores['bumps']
      
      scores['comments'] = (post['comment_count'] * comments_multiplier)
      total_score += scores['comments']
      
      scores['time'] = (time_penalty * time_penalty_multiplier * -1)
      total_score += scores['time']
      
      total_score += staff_bonus
      post['scores'] = scores

      # and save the new score
      postsdb.update_post_score(post['slug'], total_score)

      data.append({
        'username': post['user']['username'],
        'title': post['title'],
        'slug': post['slug'],
        'date_created': post['date_created'],
        'hours_elapsed': hours_elapsed,
        'bumps': post['bumps'],
        'comment_count': post['comment_count'],
        'staff_bonus': staff_bonus,
        'time_penalty': time_penalty,
        'total_score': total_score,
        'scores': scores
      })
  
    data = sorted(data, key=lambda k: k['total_score'], reverse=True)

    self.render('admin/recalc_scores.html', data=data, staff_bonus=staff_bonus, time_penalty_multiplier=time_penalty_multiplier, grace_period=grace_period, comments_multiplier=comments_multiplier, bumps_multiplier=bumps_multiplier, min_bumps=min_bumps)

###########################
### Remove user from blacklist
### /users/(?P<username>[A-z-+0-9]+)/unban
###########################
class UnBanUser(app.basic.BaseHandler):
  @tornado.web.authenticated
  def get(self, screen_name):
    if self.current_user in settings.get('staff'):
      user = userdb.get_user_by_screen_name(screen_name)
      if user:
        user['user']['is_blacklisted'] = False
        userdb.save_user(user)
    self.redirect('/')

