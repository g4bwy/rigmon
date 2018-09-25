import sys, socket, time
import pool

from worker_groups import groups


def effcolor(eff):
    if eff < 75.0:
        return "\033[91m"
    elif eff < 100.0:
        return "\033[93m"
    else:
        return "\033[92m"


class Worker(object):
    def __init__(self, addr, port=4048):
        self.addr = addr
        self.port = port

        self.reachable = False

        self.uptime = 0
        self.difficulty = 0.0
        self.hashrate = 0.0
        self.sharerate = 0.0
        self.accepted = 0
        self.rejected = 0
        self.solved = 0

    def update(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5.0)
            s.connect((self.addr, self.port))
            s.send("summary")
            l = str(s.recv(4096)).split(';')
            self.reachable = True
        except:
            self.hashrate = 0.0
            self.sharerate = 0.0
            self.reachable = False
            return
        
        for i in l:
            if i.startswith('UPTIME='):
                self.uptime = int(i.split('=')[1])

            elif i.startswith('DIFF='):
                self.difficulty = float(i.split('=')[1])

            elif i.startswith('KHS='):
                self.hashrate = float(i.split('=')[1]) * 60.0 * 1000.0

            elif i.startswith('ACCMN'):
                self.sharerate = float(i.split('=')[1])

            elif i.startswith('ACC='):
                self.accepted = int(i.split('=')[1])

            elif i.startswith('REJ='):
                self.rejected = int(i.split('=')[1])

            elif i.startswith('SOLV='):
                self.solved = int(i.split('=')[1])


class WorkerGroup(object):
    def __init__(self, pool, name, cost_fn, workers):
        self.pool = pool
        self.name = name
        self.cost_fn = cost_fn

        self.cost = 0.0
        self.reachable = 0

        self.rounds = 0
        self.real_hashrate = 0.0
        self.pool_hashrate = 0.0

        self.accepted = 0
        self.rejected = 0

        self.total_hr_eff = 0.0

        self.workers = []
        for w in workers:
            if type(w) is tuple:
                self.workers.append(Worker(*w))
            else:
                self.workers.append(Worker(w))

    def update(self):
        reachable = 0
        hashrate = 0.0
        sharerate = 0.0
        accepted = 0
        rejected = 0

        for w in self.workers:
            w.update()
            if w.reachable:
                reachable = reachable + 1
            hashrate = hashrate + w.hashrate
            sharerate = sharerate + w.sharerate
            accepted = accepted + w.accepted
            rejected = rejected + w.rejected

        self.reachable = reachable
        self.real_hashrate = hashrate
        self.sharerate = sharerate
        self.accepted = accepted
        self.rejected = rejected

        for w in self.pool.workers:
            if w['username'] == self.pool.pool['username'] + '.' + self.name:
                self.pool_hashrate = w['hashrate'] # self.pool.hashfactor
                continue

        self.rounds = self.rounds + 1

    def show(self):
        try:
            hr_eff = (self.pool_hashrate / self.real_hashrate) * 100
        except:
            hr_eff = 0.0
        try:
            sh_eff = (float(self.accepted) / (self.accepted + self.rejected)) * 100.0
        except:
            sh_eff = 0.0

        self.total_hr_eff = self.total_hr_eff + hr_eff
        avg_hr_eff = self.total_hr_eff / self.rounds

        try:
            cost_per_hm_month = self.cost_fn(len(self.workers)) / self.real_hashrate
        except:
            cost_per_hm_month = 0.0
        try:
            avg_wk_hashrate = self.real_hashrate / len(self.workers)
        except:
            avg_wk_hashrate = 0.0

        return "| %-*s | %9.3f | %9.3f | %7.3f | %s%7.3f%%\033[0m (%s%7.3f%%\033[0m) | %2u /%2u  | %8.3f | %6u | %6u | %s%7.3f%%\033[0m | %.4f" % \
                (10, self.name, self.real_hashrate, self.pool_hashrate, self.sharerate, effcolor(hr_eff), hr_eff, effcolor(avg_hr_eff), avg_hr_eff, \
                self.reachable, len(self.workers), avg_wk_hashrate,
                self.accepted, self.rejected, effcolor(sh_eff), sh_eff, cost_per_hm_month)


if __name__ == "__main__":
    pool = pool.Pool(sys.argv[1])

    wkgs = []
    for wkg in sorted(groups.items()):
        if wkg[1].has_key("disabled"):
            continue
        wkgs.append(WorkerGroup(pool, wkg[0], wkg[1]['cost'], wkg[1]['workers']))

    rounds = 0
    total_hr_eff = 0.0

    while True:
        try:
            pool.update_workers()
        except:
            pass

        real_total = 0.0
        pool_total = 0.0
        total_sharerate = 0.0
        total_reachable = 0
        total_workers = 0
        total_accepted = 0
        total_rejected = 0

        lines = [ "\033[2J\033[;H" ]

        lines.append("----------------------------------------------------------------------------------------------------------------------")
        lines.append("|    name    | miner H/m | pool H/m  |   S/m   |     eff (+avg)      |   wks   |  H/m/wk  | accept | reject |    eff   |  cost")
        lines.append("----------------------------------------------------------------------------------------------------------------------")
        for wkg in wkgs:
            wkg.update()
            lines.append(wkg.show())
            real_total = real_total + wkg.real_hashrate
            pool_total = pool_total + wkg.pool_hashrate
            total_sharerate = total_sharerate + wkg.sharerate
            total_reachable = total_reachable + wkg.reachable
            total_workers = total_workers + len(wkg.workers)
            total_accepted = total_accepted + wkg.accepted
            total_rejected = total_rejected + wkg.rejected

        try:
            hr_eff = (pool_total / real_total) * 100.0
        except:
            hr_eff = 0.0

        try:
            sh_eff = (float(total_accepted) / (total_accepted + total_rejected)) * 100.0
        except:
            sh_eff = 0.0

        rounds = rounds + 1
        total_hr_eff = total_hr_eff + hr_eff
        avg_hr_eff = total_hr_eff / rounds

        lines.append("---------------------------------------------------------------------------------------------------------------------")
        lines.append("| %-*s | %-9.3f | %-9.3f | %-7.3f | %s%7.3f%%\033[0m (%s%7.3f%%\033[0m) |  %2u/%2u  | %8.3f | %6u | %6u | %s%7.3f%%\033[0m" % \
                    (10, "total", real_total, pool_total, total_sharerate, effcolor(hr_eff), hr_eff, effcolor(avg_hr_eff), avg_hr_eff, \
                    total_reachable, total_workers, real_total / total_workers, total_accepted, total_rejected, effcolor(sh_eff), sh_eff))

        for l in lines:
            print l
        time.sleep(10)



