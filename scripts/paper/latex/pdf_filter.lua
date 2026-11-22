-- pdf_filter.lua: typeset the preprocessed paper (build_docx.sh preprocessing, split by pdf_tools.py)
-- as a journal-style LaTeX manuscript or supplement. Run AFTER --citeproc.
--
--   * title page from the custom-style divs (Title, Authors, Affiliation, Front Matter, Keywords);
--   * "§§PAGEBREAK§§" paragraphs -> \clearpage; grey "Placeholder" spans;
--   * "**Table N. ...**" captions: main text -> float with tabular, caption above, notes below;
--     supplement -> caption paragraph + longtable (continued headers) in reading order;
--     "Note:" paragraphs (and short labelled paragraphs after them) -> small table notes;
--   * image paragraph + "**Figure N. ...**" caption -> figure float (vector PDF when it exists);
--   * display math ending in "\qquad (n)" -> numbered equation (\tag{n});
--   * "Table N", "Tables S1 and S2", "Figure 2B" ... -> internal hyperlinks when the target is in this file;
--   * booktabs tables with column widths fitted to the content (port of polish_docx.py col_widths).
local stringify = pandoc.utils.stringify

local PART = 'main'
local LW = 470.0      -- \linewidth in pt (US Letter, 2.5 cm margins: 614.3 - 142.3 = 472.0, kept a little smaller)
local TH = 650.0      -- \textheight in pt (11 in - 5 cm = 652.7)
local labels = {}
local log = {}

local function rawb(s) return pandoc.RawBlock('latex', s) end
local function rawi(s) return pandoc.RawInline('latex', s) end
local function trim(s) return (s:gsub('^%s+', ''):gsub('%s+$', '')) end
local function note(s) log[#log + 1] = s end

local WOPTS = pandoc.WriterOptions({wrap_text = 'none'})
local function tex_blocks(blocks)
  local t = trim(pandoc.write(pandoc.Pandoc(blocks), 'latex', WOPTS))
  return (t:gsub('\n\n+', ' '):gsub('\n', ' '))
end
local function tex_inlines(inlines) return tex_blocks({pandoc.Plain(inlines)}) end

-- ------------------------------------------------------------------ captions and labels
local function cap_id(blk, kind)
  if not blk or blk.t ~= 'Para' then return nil end
  local first = blk.content[1]
  if not first or first.t ~= 'Strong' then return nil end
  return stringify(first):match('^' .. kind .. ' (S?%d+[a-z]?)%.')
end

local function collect(blocks)
  for _, b in ipairs(blocks) do
    local t = cap_id(b, 'Table')
    if t then labels['tab:' .. t] = true end
    local f = cap_id(b, 'Figure')
    if f then labels['fig:' .. f] = true end
    if b.t == 'Div' then collect(b.content) end
  end
end

-- ------------------------------------------------------------------ cross-reference links
local KIND = {Table = 'tab', Tables = 'tab', Figure = 'fig', Figures = 'fig', Fig = 'fig',
              ['Fig.'] = 'fig', Figs = 'fig', ['Figs.'] = 'fig'}

-- parse a token such as "S22–S23).", "1A;", "S5b." into inlines; returns inlines, rest
local function parse_token(s, kind)
  local out = pandoc.Inlines{}
  local rest = s
  local any = false
  while true do
    local id, r = rest:match('^(S?%d+[a-z]?)(.*)$')
    if not id then break end
    any = true
    if labels[kind .. ':' .. id] then
      out:insert(pandoc.Link({pandoc.Str(id)}, '#' .. kind .. ':' .. id))
    else
      out:insert(pandoc.Str(id))
    end
    rest = r
    local dash, r2 = rest:match('^([–%-])(S?%d.*)$')
    if dash then
      out:insert(pandoc.Str(dash))
      rest = r2
    else
      break
    end
  end
  if not any then return nil end
  return out, rest
end

local function link_list(inls)
  local out = pandoc.Inlines{}
  local i, n = 1, #inls
  while i <= n do
    local el = inls[i]
    local done = false
    if el.t == 'Str' then
      local pre, word = el.text:match('^([%(%[]*)(%a+%.?)$')
      local kind = word and KIND[word]
      if kind and i + 2 <= n and inls[i + 1].t == 'Space' and inls[i + 2].t == 'Str' then
        local pieces, rest = parse_token(inls[i + 2].text, kind)
        if pieces then
          out:insert(el); out:insert(inls[i + 1])
          out:extend(pieces)
          if rest ~= '' then out:insert(pandoc.Str(rest)) end
          local k = i + 3
          -- continuation: "S1 and S2", "S1 to S3", "S1, S2"
          while rest == '' or rest == ',' do
            if rest == '' and k + 2 <= n and inls[k].t == 'Space' and inls[k + 1].t == 'Str'
                and (inls[k + 1].text == 'and' or inls[k + 1].text == 'to' or inls[k + 1].text == 'or')
                and inls[k + 2].t == 'Space' and k + 3 <= n and inls[k + 3].t == 'Str' then
              local p2, r2 = parse_token(inls[k + 3].text, kind)
              if not p2 then break end
              out:insert(inls[k]); out:insert(inls[k + 1]); out:insert(inls[k + 2])
              out:extend(p2)
              if r2 ~= '' then out:insert(pandoc.Str(r2)) end
              rest, k = r2, k + 4
            elseif rest == ',' and k + 1 <= n and inls[k].t == 'Space' and inls[k + 1].t == 'Str' then
              local p2, r2 = parse_token(inls[k + 1].text, kind)
              if not p2 then break end
              out:insert(inls[k])
              out:extend(p2)
              if r2 ~= '' then out:insert(pandoc.Str(r2)) end
              rest, k = r2, k + 2
            else
              break
            end
          end
          i = k
          done = true
        end
      end
    end
    if not done then
      out:insert(el)
      i = i + 1
    end
  end
  return out
end

local link_filter = {
  traverse = 'topdown',
  Strong = function(el)
    if stringify(el):match('^Table S?%d+[a-z]?%.') or stringify(el):match('^Figure S?%d+[a-z]?%.') then
      return el, false
    end
  end,
  Link = function(el) return el, false end,
  Inlines = function(inls) return link_list(inls) end,
}

-- ------------------------------------------------------------------ inline rewrites
local function breakable(t)
  t = t:gsub('/', '/\\allowbreak{}')
  t = t:gsub('\\_', '\\_\\allowbreak{}')
  return t
end

local inline_filter = {
  Span = function(el)
    if el.attributes['custom-style'] == 'Placeholder' then
      local out = pandoc.Inlines{rawi('\\textcolor{placeholder}{')}
      out:extend(el.content)
      out:insert(rawi('}'))
      return out
    end
  end,
  Code = function(el)
    return rawi(breakable(tex_inlines({el})))
  end,
  Str = function(el)
    if utf8.len(el.text) and utf8.len(el.text) > 18 and el.text:find('[/_]') then
      return rawi(breakable(tex_inlines({el})))
    end
  end,
  Math = function(m)
    if m.mathtype == 'DisplayMath' then
      local body, num = m.text:match('^(.-)%s*\\qquad%s*%((%d+)%)%s*$')
      if body then
        labels['eq:' .. num] = true
        return rawi('\\begin{equation}' .. trim(body) .. '\\tag{' .. num .. '}\\label{eq:' .. num ..
                    '}\\end{equation}')
      end
    end
  end,
}

-- ------------------------------------------------------------------ tables
-- Times-like advance widths (em) for estimating column widths
local LOWER = {0.444, 0.5, 0.444, 0.5, 0.444, 0.333, 0.5, 0.5, 0.278, 0.278, 0.5, 0.278, 0.778, 0.5, 0.5, 0.5,
               0.5, 0.333, 0.389, 0.278, 0.5, 0.5, 0.722, 0.5, 0.5, 0.444}
local UPPER = {0.722, 0.667, 0.667, 0.722, 0.611, 0.556, 0.722, 0.722, 0.333, 0.389, 0.722, 0.611, 0.889, 0.722,
               0.722, 0.556, 0.722, 0.667, 0.556, 0.611, 0.722, 0.722, 0.944, 0.722, 0.722, 0.611}
local function est(s, pt, bold)
  local w = 0
  for _, c in utf8.codes(s) do
    if c >= 48 and c <= 57 then w = w + 0.50
    elseif c >= 97 and c <= 122 then w = w + LOWER[c - 96]
    elseif c >= 65 and c <= 90 then w = w + UPPER[c - 64]
    elseif c == 32 or c == 160 then w = w + 0.25
    elseif c == 46 or c == 44 or c == 58 or c == 59 or c == 39 then w = w + 0.25
    elseif c == 40 or c == 41 or c == 91 or c == 93 or c == 47 or c == 124 then w = w + 0.333
    elseif c == 0x2212 or c == 43 or c == 61 or c == 0xB1 or c == 0x2264 or c == 0x2265 or c == 60 or c == 62
        or c == 0xD7 then w = w + 0.564
    elseif c == 0x2013 or c == 45 then w = w + 0.5
    elseif c == 37 then w = w + 0.833
    else w = w + 0.6 end
  end
  if bold then w = w * 1.10 end
  return w * pt * 1.02
end

local function plain(blocks)
  local s = stringify(blocks)
  s = s:gsub('\\%a+', 'x'):gsub('[{}^_$]', '')
  return trim(s)
end

local SIGNS = {'+', '-', '−', '–', '—', '<', '>', '≤', '≥', '~', '±'}
local function is_num_cell(s)
  local t = trim(s)
  if t == '' then return nil end
  local changed = true
  while changed do
    changed = false
    for _, p in ipairs(SIGNS) do
      if t:sub(1, #p) == p then t = t:sub(#p + 1); changed = true end
    end
    local t2 = t:gsub('^%s+', '')
    if t2 ~= t then t = t2; changed = true end
  end
  if t == '' then return true end
  if t:match('^%.?%d') then
    for wd in s:gmatch('%a+') do if #wd >= 4 then return false end end
    return true
  end
  local low = trim(s):lower()
  return low == 'n/a' or low == 'na'
end

local SIZES = {
  {cmd = '\\footnotesize', pt = 9, tcs = 4.5, name = 'footnotesize'},
  {cmd = '\\scriptsize', pt = 8, tcs = 3.5, name = 'scriptsize'},
}

local function sum(t) local s = 0 for _, v in ipairs(t) do s = s + v end return s end

local function words_of(s, pt, bold)
  local ws = {}
  for w in s:gmatch('%S+') do
    if utf8.len(w) and utf8.len(w) > 18 and w:find('[/_]') then
      for p in w:gmatch('[^/_]+[/_]?') do ws[#ws + 1] = est(p, pt, bold) end
    else
      ws[#ws + 1] = est(w, pt, bold)
    end
  end
  return ws
end

local function nlines(words, w, space)
  local lines, cur = 1, 0
  for _, ww in ipairs(words) do
    if cur == 0 then cur = ww
    elseif cur + space + ww <= w + 0.01 then cur = cur + space + ww
    else lines = lines + 1; cur = ww end
  end
  return lines
end

-- Column widths that minimise the table height: objective = sum over rows of the tallest cell (header
-- row weighted 0.7) plus a small cost per line in every cell (0.4 in numeric columns, 0.12 in text
-- columns, so wrapping numbers costs more than wrapping words). Start every column at its longest
-- word, give width greedily to the column with the best gain per point, spread any leftover, then
-- improve by moving width between pairs of columns (first-improvement hill climbing).
local function plan(g, lw, sz, protect)
  local pad = 2 * sz.tcs
  local space = 0.25 * sz.pt
  local ncols = g.ncols
  local rows = {}
  for _, r in ipairs(g.head_txt) do rows[#rows + 1] = {r, true} end
  for _, r in ipairs(g.body_txt) do if not r.section then rows[#rows + 1] = {r, false} end end
  local W, minw, natw, bodyw = {}, {}, {}, {}
  for i, rb in ipairs(rows) do
    W[i] = {}
    for j = 1, ncols do
      local ws = words_of(rb[1][j] or '', sz.pt, rb[2])
      W[i][j] = ws
      local mx, nat = 0, 0
      for k, x in ipairs(ws) do mx = math.max(mx, x); nat = nat + x + (k > 1 and space or 0) end
      minw[j] = math.max(minw[j] or 1, mx)
      natw[j] = math.max(natw[j] or 1, nat)
      if not rb[2] then bodyw[j] = math.max(bodyw[j] or 0, nat) end
    end
  end
  if protect then   -- numeric columns keep each body cell on one line (polish_docx.py does the same)
    for j = 1, ncols do
      if g.align[j] == 'r' and (bodyw[j] or 0) <= 0.30 * lw then minw[j] = math.max(minw[j], bodyw[j] or 0) end
    end
  end
  local avail = lw - ncols * pad
  if sum(natw) <= avail then return {mode = 'natural', w = natw, h = #rows, prot = protect} end
  local w = {}
  for j = 1, ncols do w[j] = minw[j] end
  if sum(w) > avail then return nil end
  local rw, cw = {}, {}
  for i = 1, #rows do rw[i] = rows[i][2] and 0.7 or 1.0 end
  for j = 1, ncols do cw[j] = (g.align[j] == 'r') and 0.4 or 0.12 end
  local L = {}
  for i = 1, #rows do
    L[i] = {}
    for j = 1, ncols do L[i][j] = nlines(W[i][j], w[j], space) end
  end
  -- objective with columns a/b replaced by the line vectors ca/cb (optional)
  local function obj(a, ca, b, cb)
    local h = 0
    for i = 1, #rows do
      local m, t = 0, 0
      for j = 1, ncols do
        local l = L[i][j]
        if j == a then l = ca[i] elseif j == b then l = cb[i] end
        if l > m then m = l end
        t = t + cw[j] * l
      end
      h = h + rw[i] * m + t
    end
    return h
  end
  local function colines(j, width)
    local c = {}
    for i = 1, #rows do c[i] = nlines(W[i][j], width, space) end
    return c
  end
  local H = obj()
  local budget = avail - sum(w)
  local steps = {1, 2, 4, 8, 16, 32, 64, 128}
  while budget > 0.5 do
    local best, bj, bd, bcol, bh = 0
    for j = 1, ncols do
      if w[j] < natw[j] - 0.01 then
        local cands = {}
        for _, d in ipairs(steps) do cands[#cands + 1] = d end
        cands[#cands + 1] = natw[j] - w[j]
        for _, d in ipairs(cands) do
          if d <= budget and d > 0 and w[j] + d <= natw[j] + 0.01 then
            local col = colines(j, w[j] + d)
            local hn = obj(j, col)
            local gain = H - hn
            if gain > 1e-9 and gain / d > best then best, bj, bd, bcol, bh = gain / d, j, d, col, hn end
          end
        end
      end
    end
    if not bj then break end
    w[bj] = w[bj] + bd
    for i = 1, #rows do L[i][bj] = bcol[i] end
    budget = budget - bd
    H = bh
  end
  -- leftover width: to columns still short of their natural width, then to all in proportion
  if budget > 0.5 then
    local short = 0
    for j = 1, ncols do short = short + math.max(natw[j] - w[j], 0) end
    if short > 0 then
      local give = math.min(budget, short)
      for j = 1, ncols do w[j] = w[j] + give * math.max(natw[j] - w[j], 0) / short end
      budget = budget - give
    end
    if budget > 0.5 then
      local tot = sum(w)
      for j = 1, ncols do w[j] = w[j] + budget * w[j] / tot end
    end
    for j = 1, ncols do
      local c = colines(j, w[j])
      for i = 1, #rows do L[i][j] = c[i] end
    end
    H = obj()
  end
  -- pairwise transfers
  for _ = 1, 80 do
    local moved = false
    for a = 1, ncols do
      for b = 1, ncols do
        if a ~= b and w[b] < natw[b] - 0.01 then
          for _, d in ipairs({48, 24, 12, 6, 3}) do
            if w[a] - d >= minw[a] then
              local ca, cb = colines(a, w[a] - d), colines(b, w[b] + d)
              local hn = obj(a, ca, b, cb)
              if hn < H - 1e-6 then
                w[a], w[b] = w[a] - d, w[b] + d
                for i = 1, #rows do L[i][a], L[i][b] = ca[i], cb[i] end
                H, moved = hn, true
                break
              end
            end
          end
        end
      end
    end
    if not moved then break end
  end
  local hreal = 0
  for i = 1, #rows do local m = 0 for j = 1, ncols do m = math.max(m, L[i][j]) end hreal = hreal + m end
  return {mode = 'p', w = w, h = hreal, prot = protect}
end

local function colspec(p, align, ncols, sz)
  local s = '@{}'
  if p.mode == 'natural' then
    for j = 1, ncols do s = s .. align[j] end
    return s .. '@{}'
  end
  local pad = 2 * sz.tcs
  local total = sum(p.w) + ncols * pad
  for j = 1, ncols do
    local cut = pad
    if j == 1 then cut = cut - sz.tcs end
    if j == ncols then cut = cut - sz.tcs end
    local al = '\\raggedright'
    if align[j] == 'r' then al = '\\raggedleft' elseif align[j] == 'c' then al = '\\centering' end
    s = s .. string.format('>{%s\\arraybackslash}p{\\dimexpr %.4f\\linewidth-%.1fpt\\relax}', al,
                           (p.w[j] + pad) / total, cut)
  end
  return s .. '@{}'
end

local ALIGN = {AlignLeft = 'l', AlignRight = 'r', AlignCenter = 'c'}

-- keep "(-0.64 to -0.21)" and "[-0.58, -0.21]" on one line (as polish_docx.py does)
local function nbci(s, tie)
  s = s:gsub('%(([^%s()]+) to ([^%s()]+)%)', '(%1' .. tie .. 'to' .. tie .. '%2)')
  s = s:gsub('%[([^%s%[%]]+), ([^%s%[%]]+)%]', '[%1,' .. tie .. '%2]')
  return s
end

local function grid(tbl)
  local ncols = #tbl.colspecs
  local head_tex, head_txt = {}, {}
  for _, row in ipairs(tbl.head.rows) do
    local tx, pl = {}, {}
    for j, cell in ipairs(row.cells) do
      tx[j] = nbci(tex_blocks(cell.contents), '~')
      pl[j] = nbci(plain(cell.contents), '\u{A0}')
    end
    head_tex[#head_tex + 1] = tx
    head_txt[#head_txt + 1] = pl
  end
  local body_tex, body_txt = {}, {}
  for _, tb in ipairs(tbl.bodies) do
    for _, row in ipairs(tb.body) do
      local tx, pl = {}, {}
      for j, cell in ipairs(row.cells) do
        tx[j] = nbci(tex_blocks(cell.contents), '~')
        pl[j] = nbci(plain(cell.contents), '\u{A0}')
      end
      local section = ncols > 2 and pl[1] ~= ''
      for j = 2, ncols do if (pl[j] or '') ~= '' then section = false end end
      pl.section, tx.section = section, section
      body_tex[#body_tex + 1] = tx
      body_txt[#body_txt + 1] = pl
    end
  end
  -- header text used for widths: the longest header row per column
  local head1 = {}
  for j = 1, ncols do
    local best = ''
    for _, r in ipairs(head_txt) do if #(r[j] or '') > #best then best = r[j] end end
    head1[j] = best
  end
  local align = {}
  for j = 1, ncols do
    local a = ALIGN[tbl.colspecs[j][1]]
    if not a then
      if j == 1 then
        a = 'l'
      else
        local cells, hits, digit = 0, 0, false
        for _, r in ipairs(body_txt) do
          local c = r[j] or ''
          if not r.section and trim(c) ~= '' then
            cells = cells + 1
            if is_num_cell(c) then hits = hits + 1 end
            if c:find('%d') then digit = true end
          end
        end
        a = (cells > 0 and hits / cells >= 0.9 and digit) and 'r' or 'l'
      end
    end
    align[j] = a
  end
  return {ncols = ncols, head_tex = head_tex, head_txt = head_txt, head1 = head1, body_tex = body_tex, body_txt = body_txt,
          align = align}
end

-- 9 pt unless it needs many more lines than 8 pt (or cannot fit, or is too tall for a float page)
-- Candidates: 9 or 8 pt, numeric cells kept on one line (protected) or free to wrap. Score = estimated
-- height in pt, x1.25 when numbers may wrap and x1.35 at 8 pt (so 8 pt wins only when it keeps
-- numbers whole or saves much height); a natural-width 9 pt table always wins.
-- With max_hpt (main-text float tables: 8 pt penalised x1.7), candidates taller than that are used only if
-- nothing else fits.
local function choose(g, lw, max_hpt)
  local cands = {}
  for k, sz in ipairs(SIZES) do
    for _, prot in ipairs({true, false}) do
      local p = plan(g, lw, sz, prot)
      if p then
        if p.mode == 'natural' and k == 1 then return p, sz end
        local hpt = p.h * sz.pt * 1.2 * 1.2 + 30
        local score = hpt * (prot and 1 or 1.25) * (k == 1 and 1 or (max_hpt and 1.7 or 1.35))
        cands[#cands + 1] = {p = p, sz = sz, hpt = hpt, score = score}
        if max_hpt then note(string.format('  candidate %s %s: %d lines, %.0f pt, score %.0f (max %.0f)', sz.name,
                                          prot and 'protected' or 'free', p.h, hpt, score, max_hpt)) end
      end
    end
  end
  if #cands == 0 then return nil end
  table.sort(cands, function(a, b) return a.score < b.score end)
  if max_hpt then
    for _, c in ipairs(cands) do if c.hpt <= max_hpt then return c.p, c.sz end end
    local lo = cands[1]
    for _, c in ipairs(cands) do if c.hpt < lo.hpt then lo = c end end
    return lo.p, lo.sz
  end
  return cands[1].p, cands[1].sz
end

local function height_pt(p, sz)
  return p.h * sz.pt * 1.2 * 1.2 + 30
end

local function rows_tex(g, sz, p)
  local function row(cells, bold)
    local t = {}
    for j = 1, g.ncols do
      local x = cells[j] or ''
      if bold and x ~= '' then x = '\\textbf{' .. x .. '}' end
      t[j] = x
    end
    return table.concat(t, ' & ') .. ' \\\\'
  end
  local head = {}
  for _, r in ipairs(g.head_tex) do head[#head + 1] = row(r, true) end
  local body = {}
  for k, r in ipairs(g.body_tex) do
    if r.section then
      local spec = (p.mode == 'natural') and '@{}l@{}' or '@{}p{\\linewidth}@{}'
      body[#body + 1] = (k > 1 and '\\addlinespace[3pt]\n' or '') ..
          string.format('\\multicolumn{%d}{%s}{%s} \\\\', g.ncols, spec, r[1])
    else
      body[#body + 1] = row(r, false)
    end
  end
  return table.concat(head, '\n'), table.concat(body, '\n')
end

local table_count, table_log = 0, {}

-- returns latex string, landscape flag
local function table_latex(tbl, label, float, max_hpt)
  local g = grid(tbl)
  local p, sz = choose(g, LW, max_hpt)
  local land = false
  if not p then
    p, sz = choose(g, TH)
    land = p ~= nil
    if not p then
      sz = SIZES[#SIZES]
      note(string.format('WARNING table %s does not fit even in landscape', label or '?'))
      local ws = {}
      for j = 1, g.ncols do ws[j] = 1 end
      p = {mode = 'p', w = ws, h = 40}
    end
  end
  table_count = table_count + 1
  local wl = {}
  for j = 1, g.ncols do wl[j] = string.format('%.0f%s', p.w[j], g.align[j]) end
  table_log[#table_log + 1] = string.format('%s: %d cols, %s, %s%s, ~%d lines%s [%s]', label or '(unlabelled)', g.ncols,
                                            sz.name, p.mode, p.prot and ' protected' or '', p.h,
                                            land and ', landscape' or '', table.concat(wl, ' '))
  local hpt = height_pt(p, sz)
  local spec = colspec(p, g.align, g.ncols, sz)
  local head, body = rows_tex(g, sz, p)
  local pre = string.format('\\begingroup\\setstretch{1}%s\\setlength{\\tabcolsep}{%.1fpt}' ..
                            '\\renewcommand{\\arraystretch}{1.2}', sz.cmd, sz.tcs)
  if float then
    local c = (p.mode == 'natural') and '\\centering' or ''
    return pre .. c .. '\n\\begin{tabular}{' .. spec .. '}\n\\toprule\n' .. head .. '\n\\midrule\n' .. body ..
           '\n\\bottomrule\n\\end{tabular}\\par\\endgroup', land, hpt
  end
  local cont = ''
  if label then
    cont = string.format('\\multicolumn{%d}{@{}l}{\\textit{Table %s (continued)}} \\\\[2pt]\n', g.ncols, label)
  end
  return pre .. '\n\\begin{longtable}[c]{' .. spec .. '}\n\\toprule\n' .. head .. '\n\\midrule\n\\endfirsthead\n' ..
         cont .. '\\toprule\n' .. head .. '\n\\midrule\n\\endhead\n\\bottomrule\n\\endfoot\n\\bottomrule\n' ..
         '\\endlastfoot\n' .. body .. '\n\\end{longtable}\n\\endgroup', land, hpt
end

-- ------------------------------------------------------------------ paragraphs around tables/figures
local function starts_note(b)
  if not b or b.t ~= 'Para' then return false end
  local s = stringify(b)
  return s:match('^Notes?:') ~= nil
end

local function labelled(b)
  -- a short capitalised label of 1 to 3 words, then a colon (polish_docx.py FOLLOW_LBL)
  if not b or b.t ~= 'Para' then return false end
  local s = stringify(b)
  local lbl = s:match('^([^:]+):%s')
  if not lbl or #lbl > 40 or not lbl:match('^%u') then return false end
  local nw = 0
  for w in lbl:gmatch('%S+') do
    nw = nw + 1
    if not w:match('^[%w%-‐–—]+$') then return false end
  end
  return nw >= 1 and nw <= 3
end

local function emph_label(inls)
  -- italicise the leading "Label:" (up to the first Str ending in ':')
  local out = pandoc.Inlines{}
  for k, el in ipairs(inls) do
    if el.t == 'Str' and el.text:match(':$') then
      local lab = pandoc.Inlines{}
      for q = 1, k do lab:insert(inls[q]) end
      out:insert(pandoc.Emph(lab))
      for q = k + 1, #inls do out:insert(inls[q]) end
      return out
    end
    if k > 6 then break end
  end
  return inls
end

local function note_tex(b)
  return '{\\footnotesize\\setstretch{1}\\noindent ' .. tex_inlines(emph_label(b.content)) .. '\\par}'
end

local function caption_tex(b)
  return '{\\small\\setstretch{1}\\noindent ' .. tex_inlines(b.content) .. '\\par}'
end

local function is_panel(b)
  return b and b.t == 'Para' and stringify(b):match('^Panel %u%.') ~= nil
end

local function panel_tex(b)
  local c = b.content
  local out = pandoc.Inlines{}
  if #c >= 3 then
    out:insert(pandoc.Strong({c[1], c[2], c[3]}))
    for q = 4, #c do out:insert(c[q]) end
  else
    out = c
  end
  return '\\par\\Needspace{6\\baselineskip}\\vspace{4pt}{\\small\\setstretch{1}\\noindent ' .. tex_inlines(out) ..
         '\\par}\\nopagebreak\\vspace{2pt}'
end

local function image_para(b)
  if not b or b.t ~= 'Para' then return nil end
  local img
  for _, el in ipairs(b.content) do
    if el.t == 'Image' then
      if img then return nil end
      img = el
    elseif el.t ~= 'Space' and el.t ~= 'SoftBreak' then
      return nil
    end
  end
  return img
end

local function file_exists(p)
  local f = io.open(p, 'r')
  if f then f:close() return true end
  return false
end

local fig_log = {}
local function figure_latex(img, cap, fid, followers)
  local src = img.src
  local pdf = src:gsub('%.png$', '.pdf')
  if pdf ~= src and file_exists(pdf) then src = pdf end
  local w = img.attributes.width or ''
  local inches = tonumber(w:match('^([%d.]+)in$') or '')
  local width = '\\linewidth'
  if inches and inches < 6.4 then width = string.format('%.2fin', inches) end
  local captext = stringify(cap)
  for _, f in ipairs(followers) do captext = captext .. ' ' .. stringify(f) end
  local lines = math.ceil(est(captext, 10) / LW) + 1 + #followers
  local maxh = TH - lines * 12.5 - 28
  if maxh > 0.80 * TH then maxh = 0.80 * TH end
  fig_log[#fig_log + 1] = string.format('Figure %s: %s (max height %.0f pt, caption ~%d lines)', fid, src, maxh, lines)
  local parts = {
    '\\begin{figure}[' .. (PART == 'main' and 'tbp' or 'H') .. ']',
    '\\centering',
    '\\phantomsection\\label{fig:' .. fid .. '}%',
    string.format('\\includegraphics[width=%s,height=%.0fpt,keepaspectratio]{%s}', width, maxh, src),
    '\\par\\vspace{6pt}',
    '{\\small\\setstretch{1}\\leftskip=0pt\\rightskip=0pt\\parfillskip=0pt plus 1fil\\noindent ' ..
      tex_inlines(cap.content) .. '\\par}',
  }
  for _, f in ipairs(followers) do
    parts[#parts + 1] = '\\vspace{2pt}{\\footnotesize\\setstretch{1}\\leftskip=0pt\\rightskip=0pt' ..
                        '\\parfillskip=0pt plus 1fil\\noindent ' .. tex_inlines(emph_label(f.content)) .. '\\par}'
  end
  parts[#parts + 1] = '\\end{figure}'
  return table.concat(parts, '\n')
end

-- ------------------------------------------------------------------ title-page divs
local function style_div(div, style)
  local x = tex_blocks(div.content)
  if style == 'Title' then
    local rest = x:match('^Supplementary Information for:%s*(.*)$')
    if rest then
      return rawb('\\thispagestyle{plain}\\noindent{\\large Supplementary Information for:\\par}\\vspace{6pt}' ..
                  '\\noindent{\\LARGE\\bfseries\\raggedright ' .. rest .. '\\par}\\vspace{14pt}')
    end
    return rawb('\\thispagestyle{plain}\\vspace*{6pt}\\noindent{\\LARGE\\bfseries\\raggedright ' .. x ..
                '\\par}\\vspace{18pt}')
  elseif style == 'Authors' then
    return rawb('\\noindent{\\large ' .. x .. '\\par}\\vspace{10pt}')
  elseif style == 'Affiliation' then
    return rawb('\\noindent{\\small ' .. x .. '\\par}\\vspace{2pt}')
  elseif style == 'Front Matter' then
    return rawb('\\vspace{10pt}\\noindent{\\small ' .. x .. '\\par}')
  elseif style == 'Keywords' then
    return rawb('\\par\\vspace{10pt}\\noindent ' .. x .. '\\par')
  end
  return nil
end

-- ------------------------------------------------------------------ block processing
local PAGEBREAK = '§§PAGEBREAK§§'

local function process(blocks)
  local out = pandoc.Blocks{}
  local i, n = 1, #blocks
  local cur_label
  while i <= n do
    local b = blocks[i]
    local tid = cap_id(b, 'Table')
    if b.t == 'Para' and stringify(b) == PAGEBREAK then
      out:insert(rawb('\\clearpage'))
      i = i + 1
    elseif b.t == 'Div' and b.attributes['custom-style'] then
      local r = style_div(b, b.attributes['custom-style'])
      if r then out:insert(r) else out:extend(process(b.content)) end
      i = i + 1
    elseif b.t == 'Div' and b.identifier == 'refs' then
      out:insert(rawb('\\begingroup\\small\\setstretch{1.05}'))
      out:insert(b)
      out:insert(rawb('\\endgroup'))
      i = i + 1
    elseif b.t == 'Div' then
      b.content = process(b.content)
      out:insert(b)
      i = i + 1
    elseif tid and PART == 'main' and blocks[i + 1] and blocks[i + 1].t == 'Table' then
      local j = i + 2
      local first = true
      local textlen = est(stringify(b), 10)
      local notes = {}
      while j <= n and (starts_note(blocks[j]) or (not first and labelled(blocks[j]))) do
        notes[#notes + 1] = '\\vspace{3pt}' .. note_tex(blocks[j])
        textlen = textlen + est(stringify(blocks[j]), 9) + 0.5 * LW
        first = false
        j = j + 1
      end
      local text_h = textlen / LW * 11.5 + 20
      local tex, land, hpt = table_latex(blocks[i + 1], tid, true, TH - 10 - text_h)
      local parts = {'\\begin{table}[tbp]', '\\phantomsection\\label{tab:' .. tid .. '}%', caption_tex(b),
                     '\\vspace{5pt}', tex}
      for _, x in ipairs(notes) do parts[#parts + 1] = x end
      parts[#parts + 1] = '\\end{table}'
      local total = hpt + text_h
      note(string.format('Table %s float: estimated height %.0f pt of %.0f', tid, total, TH))
      if total > TH - 10 then
        note('NOTE Table ' .. tid .. ' estimated taller than a page (estimate is conservative); check the page')
      end
      local s = table.concat(parts, '\n')
      if land then s = '\\begin{landscape}\n' .. s .. '\n\\end{landscape}' end
      out:insert(rawb(s))
      i = j
    elseif tid then
      cur_label = tid
      out:insert(rawb('\\par\\Needspace{8\\baselineskip}\\vspace{8pt}\\phantomsection\\label{tab:' .. tid .. '}%\n' ..
                      caption_tex(b) .. '\\nopagebreak\\vspace{3pt}'))
      i = i + 1
    elseif b.t == 'Table' then
      local tex, land = table_latex(b, cur_label, false)
      if land then tex = '\\begin{landscape}\n' .. tex end
      local j = i + 1
      local notes = {}
      local first = true
      while j <= n and (starts_note(blocks[j]) or (not first and labelled(blocks[j]))) do
        notes[#notes + 1] = note_tex(blocks[j])
        first = false
        j = j + 1
      end
      if #notes > 0 then tex = tex .. '\n\\vspace{2pt}' .. table.concat(notes, '\n\\vspace{2pt}') end
      if land then tex = tex .. '\n\\end{landscape}' end
      out:insert(rawb(tex .. '\n\\vspace{8pt}'))
      i = j
    elseif b.t == 'Header' and (cap_id(blocks[i + 1], 'Table') or cap_id(blocks[i + 2], 'Table')) then
      -- keep a heading with the table caption that follows it
      out:insert(rawb('\\Needspace{14\\baselineskip}'))
      out:insert(b)
      i = i + 1
    elseif is_panel(b) then
      out:insert(rawb(panel_tex(b)))
      i = i + 1
    elseif image_para(b) and cap_id(blocks[i + 1], 'Figure') then
      local fid = cap_id(blocks[i + 1], 'Figure')
      local j = i + 2
      local followers = {}
      while j <= n and labelled(blocks[j]) and not starts_note(blocks[j]) do
        followers[#followers + 1] = blocks[j]
        j = j + 1
      end
      out:insert(rawb(figure_latex(image_para(b), blocks[i + 1], fid, followers)))
      i = j
    else
      local prev = (i > 1 and blocks[i - 1].t == 'Para' and #blocks[i - 1].content == 1) and blocks[i - 1].content[1]
      local after_display = prev and ((prev.t == 'RawInline' and prev.text:match('^\\begin{equation}'))
                                      or (prev.t == 'Math' and prev.mathtype == 'DisplayMath'))
      if b.t == 'Para' and after_display and b.content[1] and b.content[1].t == 'Str'
          and b.content[1].text:match('^%l') then
        b.content:insert(1, rawi('\\noindent '))
      end
      out:insert(b)
      i = i + 1
    end
  end
  return out
end

function Pandoc(doc)
  PART = stringify(doc.meta.pdfpart or 'main')
  collect(doc.blocks)
  doc = doc:walk(link_filter)
  doc = doc:walk(inline_filter)
  doc.blocks = process(doc.blocks)
  io.stderr:write(string.format('[pdf_filter] %s: %d tables\n', PART, table_count))
  for _, l in ipairs(table_log) do io.stderr:write('  table ' .. l .. '\n') end
  for _, l in ipairs(fig_log) do io.stderr:write('  ' .. l .. '\n') end
  for _, l in ipairs(log) do io.stderr:write('  ' .. l .. '\n') end
  return doc
end
