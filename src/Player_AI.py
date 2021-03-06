"""Player_AI.py - Contains the AI object that can clontrol a player"""

#     This part of mPyre, a python implementation of the game Empire
#     Copyright (C) 2019  Robert C. Ramsdell III <rcriii42@gmail.com>
#
#     mPyre is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     mPyre is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with mPyre.  If not, see <https://www.gnu.org/licenses/>.
#
#     Work on this file started on 25 January, 2020

import pygame.time
from pygame.locals import K_KP1, K_KP2, K_KP3, K_KP4, K_KP6, K_KP7, K_KP8, K_KP9
import random
from copy import copy
from BaseObjects import Unit, a_star, Map
from Cities import City
from GroundUnits import Infantry

try:
    _choices = random.choices
except AttributeError:
    #print("Using user-defined choices")
    import choices
    _choices = choices.choices


class AI():
    """An AI to control a player"""
    def __init__(self, player, game):
        self.player = player
        self.game = game

        self.moving_unit = None
        self.moving_unit_selected = True

        self.base_scores = {City: 100,
                            Infantry: 100}
        self.assigned_targets = {}

    def next_move(self):
        """Determine my next move

        return a list with messages for the game window:
        'End_Turn': end my turn
        'select', Unit: select the given unit
        'move', Unit, key: move the given unit in the direction indicated by key
        """
        pygame.time.wait(450)
        self.moving_unit = self.player.next_to_move()
        if self.moving_unit and not self.moving_unit_selected:
            self.moving_unit_selected = True
            #print("{} selected".format(self.moving_unit.name))
            return ['select', self.moving_unit]
        elif self.moving_unit:
            t = self.select_target(self.moving_unit)
            dir, key = self.move_unit(t)
            if dir and key:
                # print("{} target is {}, moving {}".format(self.moving_unit.name,
                #                                          t.name,
                #                                           dir))
                return ['move', self.moving_unit, key]
            else:
                self.moving_unit.moved = self.moving_unit.move_speed
                self.moving_unit.selected = False
                self.moving_unit = None
        else:
            self.moving_unit_selected = False
            return ["End Turn"]

    def move_unit(self, target):
        """Move the moving_unit towards the target if it can"""
        dir = self.moving_unit.direction_to(target)
        print("{}'s {} at {} moving to {} path:".format(self.player.name,
                                                        self.moving_unit.name,
                                                        self.moving_unit.coords,
                                                        target.coords))
        adj_map = copy(self.game.map)
        for u in self.player.units:
            adj_map[u.coords] = 'edge' #mark friendly units as impassible
        path_to_target = a_star(self.moving_unit.coords, target.coords, adj_map,
                                self.moving_unit.cannot_enter)
        if path_to_target:
            new_coords = path_to_target[1]
        else:
            return False, False
        print("{}".format(path_to_target))
        print("{}: {}".format(new_coords,
                              self.game.map[new_coords]))
        while True:
            u = self.moving_unit.check_collision(new_coords, self.game)
            if isinstance(u, City):
                break
            elif isinstance(u, Unit) and not (self.moving_unit.owner is u.owner):
                break
            elif self.game.map[new_coords] in self.moving_unit.cannot_enter or u:
                new_dir = {( 0,  1): ( 1,  1),  #adjust movement clockwise
                           ( 1,  1): ( 1,  0),
                           ( 1,  0): ( 1, -1),
                           ( 1, -1): ( 0, -1),
                           ( 0, -1): (-1, -1),
                           (-1, -1): (-1,  0),
                           (-1,  0): (-1,  1),
                           (-1,  1): ( 0,  1)}[dir]
                new_coords = (self.moving_unit.coords[0] + new_dir[0],
                              self.moving_unit.coords[1] + new_dir[1])
                #print("move unit found collision {} {}".format(dir, new_dir))
                dir = new_dir
            else:
                break
        key = {( 0,  1): K_KP2,
               ( 1,  1): K_KP3,
               ( 1,  0): K_KP6,
               ( 1, -1): K_KP9,
               ( 0, -1): K_KP8,
               (-1, -1): K_KP7,
               (-1,  0): K_KP4,
               (-1,  1): K_KP1}[dir]
        return dir, key

    def select_target(self, unit):
        """Select a target randomly from the """
        targets = self.find_targets(unit)
        #print(unit.name, targets[:5])
        return _choices(targets[0][:5], weights=targets[1][:5])[0]

    def find_targets(self, unit):
        """Rank targets for the given unit"""
        cities = [c for c in self.game.cities if c.owner is not self.player]
        units = [u for u in self.game.units if u.owner is not self.player]
        scores = [(c, self.score_target(unit, c)) for c in cities]
        scores.extend([(u, self.score_target(unit, u)) for u in units])
        scores.sort(key=lambda tup: tup[1], reverse=True)
        return [t[0] for t in scores], [t[1] for t in scores]

    def score_target(self, unit, target):
        """Calculate the score for the given target and unit"""
        if isinstance(target, City):
            return self.base_scores[City] / unit.distance_to(target)
        elif isinstance(target, Infantry):
            return self.base_scores[Infantry] / unit.distance_to(target)
