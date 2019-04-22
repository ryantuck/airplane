import random

import attr

ROWS = 3
SEATS_IN_ROW = 3
T_SHUFFLE = 10
T_OVERHEAD_BIN = 10
PROB_OVERHEAD_BIN = 0.8


def random_ppl(seats):
    """
    Given a list of Seats, return a randomly-ordered list of Persons.
    """
    people = [Person(s, random.random() < PROB_OVERHEAD_BIN) for s in seats]
    random.shuffle(people)
    return people


@attr.s
class Seat:
    row = attr.ib()
    col = attr.ib()


@attr.s
class Person:

    target_seat = attr.ib()
    has_carry_on = attr.ib()

    def __attrs_post_init__(self):
        self.on_plane = False
        self.current_row = None
        self.is_seated = False
        self.t_accrued = 0
        self.t_overhead_bin_remaining = 0
        self.t_shuffling_remaining = 0

    def enter_plane(self):
        self.on_plane = True
        self.current_row = 0

    def start_overhead_bin(self):
        self.t_overhead_bin_remaining = 10

    def start_shuffling(self):
        self.t_shuffling_remaining = 10

    def move_forward(self):
        self.current_row += 1

    def in_target_row(self):
        return self.current_row == self.target_seat.row

    def in_seat(self):
        return self.is_seated

    def in_aisle(self):
        return self.on_plane and not self.in_seat()

    def is_doing_overhead_bin(self):
        return self.t_overhead_bin_remaining > 0

    def is_shuffling(self):
        return self.t_shuffling_remaining > 0

    def iterate(self):
        """
        Move towards seat if possible. Wait if otherwise. Nothing if seated.
        """
        if self.in_seat():
            return None
        elif self.in_target_row():
            if self.is_doing_overhead_bin():
                self.t_overhead_bin_remaining -= 1
            elif self.is_shuffling():
                self.t_shuffling_remaining -= 1
                # this could probably be cleaner
                if not self.is_shuffling():
                    self.is_seated = True
            else:
                self.is_seated = True
                return None
        self.t_accrued += 1
        return None


@attr.s
class Plane:

    rows = attr.ib()
    seats_per_row = attr.ib()
    seat_targets_fn = attr.ib()

    def __attrs_post_init__(self):
        self.shuffling_rows = []
        self.overhead_bin_rows = []
        self.t_accrued = 0
        self.seats = [
            Seat(r, c) for r in range(self.rows) for c in range(self.seats_per_row)
        ]
        self.people = self.seat_targets_fn(self.seats)

    def people_in_row(self, row):
        return [p for p in self.people if p.current_row == row]

    def people_in_aisle(self):
        return [p for p in self.people if p.in_aisle()]

    def people_on_plane(self):
        return [p for p in self.people if p.on_plane]

    def everyone_seated(self):
        return all(p.in_seat() is True for p in self.people)

    def iterate(self):
        """
        Take a step through the simulation.
        """
        for p in sorted(self.people_in_aisle(), key=lambda x: x.current_row, reverse=True):
            row = p.current_row
            if p.in_target_row():
                # start overhead bin if needed
                if p.has_carry_on and not p.is_doing_overhead_bin():
                    p.start_overhead_bin()
                    p.has_carry_on = False
                if not p.is_shuffling():
                    ppl_in_way = [
                        pr
                        for pr in self.people_in_row(p.current_row)
                        if pr.target_seat.col < p.target_seat.col
                    ]
                    if ppl_in_way != []:
                        # need to shuffle
                        p.start_shuffling()
                        for pp in ppl_in_way:
                            pp.start_shuffling()

            elif not any(
                p2.current_row == p.current_row + 1 for p2 in self.people_in_aisle()
            ):
                # no one in way. move forward.
                p.move_forward()

            # finally, handle iterating through time
            p.iterate()

        # get the next person on the plane
        if not any(p.current_row == 0 for p in self.people_in_aisle()):
            ppl_not_on_plane = [p for p in self.people if not p.on_plane]
            if ppl_not_on_plane != []:
                ppl_not_on_plane[0].enter_plane()

        ppl_ohb = [p for p in self.people_in_aisle() if p.is_doing_overhead_bin()]
        ppl_shuff = [p for p in self.people_in_aisle() if p.is_shuffling()]
        print(self.t_accrued, len(self.people_in_aisle()), len(ppl_ohb), len(ppl_shuff))

#        for p in self.people_on_plane():
#            print(
#                f'target: r{p.target_seat.row}c{p.target_seat.col} | '
#                f'curr_row: {p.current_row} | '
#                f'seated: {p.in_seat()} | '
#                f'aisle: {p.in_aisle()} | '
#                f'bin: {p.is_doing_overhead_bin()} | '
#                f'shuffle: {p.is_shuffling()}'
#            )

    def run_simulation(self):
        while not self.everyone_seated():
            self.iterate()
            self.t_accrued += 1


def run(rows, seats_per_row):
    """
    Run simulation.
    """
    plane = Plane(rows, seats_per_row, random_ppl)
    plane.run_simulation()
    return plane.results()


if __name__ == '__main__':
    run(ROWS, SEATS_PER_ROW)
