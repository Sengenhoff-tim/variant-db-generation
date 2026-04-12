#include <atomic>
#include <cerrno>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <mutex>
#include <ostream>
#include <queue>
#include <sstream>
#include <string>
#include <sys/types.h>
#include <vector>
#include <array>
#include <memory>
#include <thread>
#include <tuple>
#include <chrono>
#include <unordered_map>
#include <cmath>
#include <cstring>   // std::strlen, std::strerror
#include <cerrno>



#include "protein_graph.hpp"
#include "graph_loader.hpp"


#define QUEUE_SIZE 10000

template<class T, size_t MaxQueueSize>
class Queue
{
    std::condition_variable consumer_, producer_;
    std::mutex mutex_;
    using unique_lock = std::unique_lock<std::mutex>;

    std::queue<T> queue_;

public:
    template<class U>
    void push_back(U&& item) {
        unique_lock lock(mutex_);
        while(MaxQueueSize == queue_.size())
            producer_.wait(lock);
        queue_.push(std::forward<U>(item));
        consumer_.notify_one();
    }

    T pop_front() {
        unique_lock lock(mutex_);
        while(queue_.empty())
            consumer_.wait(lock);
        auto full = MaxQueueSize == queue_.size();
        auto item = queue_.front();
        queue_.pop();
        if(full)
            producer_.notify_all();
        return item;
    }
};


// TODO output queue
void thread_lifecycle(
    Queue<std::tuple<int64_t, int64_t, uint8_t>, QUEUE_SIZE>& query, 
    Queue<std::string, QUEUE_SIZE>& output_queue,
    std::vector<ProteinGraph>& pgs,
    std::atomic<bool>* pgs_executed,
    std::atomic<uint32_t>& atomic_pgs_finished,
    int64_t max_query,
    uint32_t num_bins
    ){

        bool iter_bool = false, should_execute = iter_bool;

        std::tuple<int64_t, int64_t, uint8_t> next_query;
        std::string output_benchmark = "";

        int64_t lower, upper;
        uint32_t used_bin;
        uint8_t num_vars_max;
        while(true) {
            // Get next query
            next_query = query.pop_front();

            // Stop Condition reached terminate thread
            if (std::get<2>(next_query) == uint8_t(-1)) break;

            //Set query params
            lower = std::get<0>(next_query);
            upper = std::get<1>(next_query);

            // Get the bin to use
            used_bin = (uint32_t) std::ceil( (upper / (max_query / num_bins))) - 1;
            if (used_bin >= num_bins) {
                used_bin = num_bins - 1;
            }


            // Scan bool vector
            for (uint32_t i = 0; i < pgs.size(); i++){
                // Check if it was already executed by another thread
                pgs_executed[i].compare_exchange_strong(should_execute, !iter_bool);
                if (should_execute == iter_bool) {
                    // It was not executed by another thread, execute now!
                    num_vars_max = pgs.at(i).max_vars_bins[used_bin];
                    if (num_vars_max == 255) {
                        output_benchmark += pgs.at(i).tvs_traverse_naive(lower,  upper);
                    } else {
                        output_benchmark += pgs.at(i).tvs_traverse_varcount_naive(lower,  upper, num_vars_max);
                    }


                    if (output_benchmark.length() != 0) {
                        output_queue.push_back(output_benchmark);
                        output_benchmark = "";
                    }
                    int finished_count = atomic_pgs_finished.fetch_add(1, std::memory_order_acq_rel);
                    if (finished_count >= pgs.size() - 1) {
                        //  Only 1 Thread should be active here!!!
                        // std::cerr << "Thread pushing end signal" << std::endl;
                        output_queue.push_back("TODO FINISHED CALCULATING");
                        atomic_pgs_finished.exchange(0);
                    }
                } 
                // Update should_execute due to the atomic replacing its value
                should_execute = iter_bool;
            }
            // Update bools
            iter_bool = !iter_bool;
            should_execute = iter_bool;
            
            
        }

}

int main(int argc, char *argv[]) {
    if (argc != 6) {
    std::cerr << "Usage: protgraphtraverseintvarlimitter <database.bpcsr> <query.csv> <num_threads| -1> <output.fasta> <limits.csv>\n";
    std::cerr << "Received argc=" << argc << "\n";
    for (int i = 0; i < argc; ++i) {
        std::cerr << " argv[" << i << "]=" << (argv[i] ? argv[i] : "(null)") << "\n";
    }
    return 2;
}

    if (!argv[1] || std::strlen(argv[1]) == 0) {
        std::cerr << "Error: missing or empty database filename (arg 1).\n";
        return 3;
    }
    std::string FILENAME = argv[1];
    auto idx = FILENAME.rfind('.');
    if (idx == std::string::npos) {
        std::cerr << "Error: database filename has no extension: '" << FILENAME << "'. Expected .bpcsr\n";
        return 4;
    }
    std::string extension = FILENAME.substr(idx+1);
    if (extension != "bpcsr") {
        std::cerr << "Error: unsupported database extension '" << extension << "'. Expected 'bpcsr'.\n";
        return 5;
    }

    if (!argv[2] || std::strlen(argv[2]) == 0) {
        std::cerr << "Error: missing or empty query CSV filename (arg 2).\n";
        return 6;
    }
    std::string QUERY_FILE = argv[2];
    std::ifstream query_file(QUERY_FILE);
    if (!query_file) {
        std::cerr << "Error: could not open query CSV '" << QUERY_FILE << "': " << std::strerror(errno) << "\n";
        return 7;
    }

    if (!argv[3] || std::strlen(argv[3]) == 0) {
        std::cerr << "Error: missing num_threads argument (arg 3). Use -1 for hardware concurrency.\n";
        return 8;
    }
    int num_threads = 0;
    try {
        int tmp = std::stoi(argv[3]);
        if (tmp == -1) {
            num_threads = std::max(1u, std::thread::hardware_concurrency());
        } else if (tmp > 0) {
            num_threads = tmp;
        } else {
            std::cerr << "Error: invalid num_threads value '" << argv[3] << "'. Must be -1 or positive integer.\n";
            return 9;
        }
    } catch (...) {
        std::cerr << "Error: could not parse num_threads argument '" << argv[3] << "'.\n";
        return 10;
    }

    if (!argv[4] || std::strlen(argv[4]) == 0) {
        std::cerr << "Error: missing or empty output filename (arg 4).\n";
        return 11;
    }
    std::ofstream output_file(argv[4]);
    if (!output_file) {
        std::cerr << "Error: could not open output file '" << argv[4] << "' for writing: " << std::strerror(errno) << "\n";
        return 12;
    }

    if (!argv[5] || std::strlen(argv[5]) == 0) {
        std::cerr << "Error: missing or empty limits CSV filename (arg 5).\n";
        return 13;
    }
    std::string var_limit_csv = argv[5];
    std::ifstream var_limits_if(var_limit_csv);
    if (!var_limits_if) {
        std::cerr << "Error: could not open limits CSV '" << var_limit_csv << "': " << std::strerror(errno) << "\n";
        return 14;
    }

    // proceed to read limits file, with checks for malformed lines
    std::cout << "Loading Variants" << std::endl;
    std::string var_line;
    uint32_t num_bins = 0;
    std::vector<uint64_t> bins;
    std::unordered_map<std::string, std::vector<uint8_t>> max_vars;
    while (std::getline(var_limits_if, var_line)) {
        if (var_line.empty()) continue;
        std::stringstream var_ss_line(var_line);
        std::string var_entry;
        if (!std::getline(var_ss_line, var_entry, ',')) {
            std::cerr << "Error: malformed limits line (no entries): '" << var_line << "'\n";
            return 15;
        }
        if (var_entry == "#bins") {
            if (!std::getline(var_ss_line, var_entry)) { std::cerr << "Error: malformed #bins line: '" << var_line << "'\n"; return 16; }
            try { num_bins = static_cast<uint32_t>(std::stoul(var_entry)); }
            catch (...) { std::cerr << "Error: invalid #bins value '" << var_entry << "'\n"; return 17; }
        } else if (var_entry == "bins") {
            if (num_bins == 0) { std::cerr << "Error: 'bins' encountered before '#bins' in limits file.\n"; return 18; }
            bins.clear();
            for (uint32_t i = 0; i < num_bins; ++i) {
                std::string val;
                if (!std::getline(var_ss_line, val, (i+1< num_bins ? ',' : '\n'))) {
                    std::cerr << "Error: insufficient bin values in line: '" << var_line << "'\n"; return 19;
                }
                try { bins.push_back(static_cast<uint64_t>(std::stod(val) * 1e9)); }
                catch (...) { std::cerr << "Error: invalid bin numeric value '" << val << "'\n"; return 20; }
            }
        } else {
            if (num_bins == 0) { std::cerr << "Error: protein entry encountered before '#bins' in limits file.\n"; return 21; }
            std::string protein_entry = var_entry;
            std::vector<uint8_t> vals;
            for (uint32_t i = 0; i < num_bins; ++i) {
                std::string val;
                if (!std::getline(var_ss_line, val, (i+1< num_bins ? ',' : '\n'))) {
                    std::cerr << "Error: insufficient variant columns for protein '" << protein_entry << "' in line: '" << var_line << "'\n"; return 22;
                }
                try { vals.push_back(static_cast<uint8_t>(std::stoi(val))); }
                catch (...) { std::cerr << "Error: invalid variant value '" << val << "' for protein '" << protein_entry << "'\n"; return 23; }
            }
            max_vars.emplace(std::move(protein_entry), std::move(vals));
        }
    }

    if (bins.empty()) {
        std::cerr << "Error: no bins defined in limits CSV.\n";
        return 24;
    }

    // Loading graphs
    std::cout << "Loading Graphs" << std::endl;
    GraphLoader* gl = nullptr;
    if (extension == "bpcsr") {
        gl = new GraphLoaderBinary();
    }
    if (!gl) {
        std::cerr << "Error: no graph loader available for extension '" << extension << "'.\n";
        return 25;
    }

    std::vector<ProteinGraph>* pgs = nullptr;
    try {
        pgs = gl->loadGraphs(FILENAME, max_vars);
    } catch (const std::exception &e) {
        std::cerr << "Error: exception while loading graphs: " << e.what() << "\n";
        return 26;
    }
    if (!pgs) {
        std::cerr << "Error: failed to load protein graphs from '" << FILENAME << "'.\n";
        return 27;
    }  

    

    // Set Queues
    Queue<std::tuple<int64_t, int64_t, uint8_t>, QUEUE_SIZE> query;
    Queue<std::string, QUEUE_SIZE> output_queue;

    // Set bool vector if executed
    // std::vector<bool> pgs_executed(pgs->size(), false);
    // bool* pgs_executed = new bool[pgs->size()];
    // for (int i = 0; i < pgs->size(); i++){
    //     pgs_executed[i] = false;
    // }
    std::atomic<bool>* pgs_executed = new std::atomic<bool>[pgs->size()];
    for (int i = 0; i < pgs->size(); i++){
        pgs_executed[i].exchange(false);
    }

    // Create atomic counter of executed entries
    std::atomic<uint32_t> atomic_pgs_finished{0};


    // Create Thread pool after retrieving all needed information
    std::cout << "Starting Threads" << std::endl;
    std::vector<std::thread> threads;
    for (int i = 0; i < num_threads; i++) {
        threads.push_back(std::thread(
            thread_lifecycle, // Method
            std::ref(query), std::ref(output_queue), //Params
            std::ref(*pgs), std::ref(pgs_executed),
            std::ref(atomic_pgs_finished),
            bins.back(),
            num_bins
            
        ));
    }


    // Now serve queries
    // TODO Currently we simply read a csv
    std::string line;
    std::stringstream ss_line;
    std::string entry;
    int64_t lower;
    int64_t upper;
    int query_counter = 1;

    while (std::getline(query_file, line)) {
        // Parse Query
        ss_line.clear();
        ss_line.str(line);
        std::getline(ss_line, entry, ',');
        lower = (int64_t)(std::stod(entry) * 1000000000);
        std::getline(ss_line, entry, '\n');
        upper = (int64_t)(std::stod(entry) * 1000000000);
        std::tuple<int64_t, int64_t, uint8_t> query_tuple(lower, upper, 1);

        //Submit Query
        for (int i = 0; i < num_threads; i++) {
            query.push_back(query_tuple);
        }
        // Wait for the results!
        while (true) {
            std::string output = output_queue.pop_front();
            if (output.rfind("TODO FINISHED CALCULATING", 0) == 0) { break; }
            // std::cout << output; // E.G.: here we could simply pass it through the socket
            output_file << output;

        }

        std::cerr << "Processed Query " << query_counter << " with: " << lower << ":" << upper << std::endl;
        query_counter++;
        // 18 446 744 073.709553
        //  9 223 372 036.854776
    }
    // Repeat next Query TODO 



    // Spin down
    // std::cout << "Spinning Down..." << std::endl;
    std::tuple<int64_t, int64_t, uint8_t> stop_tuple(0, 0, uint8_t(-1));
    for (int i = 0; i < num_threads*2; i++)
    {
        query.push_back(stop_tuple);
    }
    for (int i = 0; i < num_threads; i++)
    {
        threads.at(i).join();
    }

    // printf("Completely finished!\n");
    return  0;
}